import 'dart:convert';
import 'dart:ui';
import 'package:flutter/material.dart';
import 'package:web_socket_channel/web_socket_channel.dart';
import 'package:nsd/nsd.dart';
import 'package:mobile_scanner/mobile_scanner.dart';
import 'dart:async';
import 'dart:typed_data';
import 'dart:math';

void main() {
  runApp(const JackUltraApp());
}

class JackUltraApp extends StatelessWidget {
  const JackUltraApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      theme: ThemeData.dark(),
      home: const Dashboard(),
    );
  }
}

class Dashboard extends StatefulWidget {
  const Dashboard({super.key});

  @override
  State<Dashboard> createState() => _DashboardState();
}

class _DashboardState extends State<Dashboard> with SingleTickerProviderStateMixin {
  String relayUrl = '10.24.156.92:8001'; // Dynamically detected PC IP
  late WebSocketChannel channel;
  late AnimationController _animationController;
  
  double cpu = 0.0;
  double ram = 0.0;
  String status = "OFFLINE";
  List<String> logs = [];
  bool isListening = false;
  Timer? _reconnectTimer;
  bool _isConnecting = false;
  int _retryCount = 0;
  
  // New: ADB & screenshot support
  Uint8List? _lastScreenshot;
  bool _showScreenshot = false;
  List<Map<String, dynamic>> _commandHistory = [];
  bool _showCommands = true;

  @override
  void initState() {
    super.initState();
    _animationController = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 2),
    )..repeat(reverse: true);
    _discoverService();
  }

  @override
  void dispose() {
    _animationController.dispose();
    _reconnectTimer?.cancel();
    try {
       channel.sink.close();
    } catch (_) {}
    super.dispose();
  }

  void _connect() {
    if (_isConnecting) return;
    _isConnecting = true;
    
    setState(() => status = "CONNECTING...");
    _reconnectTimer?.cancel();

    try {
      final uri = Uri.parse('ws://$relayUrl/ws/jack_secure_neural_link_2026');
      logs.insert(0, "SYSTEM: Attempting link to $uri");
      
      channel = WebSocketChannel.connect(uri);
      
      channel.stream.listen((data) {
        _isConnecting = false;
        _retryCount = 0;
        try {
          final jsonData = jsonDecode(data);
          
          // Handle telemetry
          if (jsonData["type"] == "telemetry_pulsed" || jsonData.containsKey("cpu")) {
            setState(() {
              cpu = (jsonData["cpu"] ?? 0.0).toDouble();
              ram = (jsonData["ram"] ?? 0.0).toDouble();
              status = "ONLINE";
              if (logs.length > 100) logs.removeLast();
            });
          }
          // Handle command result
          else if (jsonData["type"] == "command_result") {
            setState(() {
              logs.insert(0, "RES: ${jsonData["result"]}");
              if (logs.length > 100) logs.removeLast();
            });
          }
          // Handle screenshot update
          else if (jsonData["type"] == "screenshot_update" && jsonData.containsKey("data")) {
            try {
              final b64 = jsonData["data"];
              final bytes = base64Decode(b64);
              setState(() {
                _lastScreenshot = bytes;
                _showScreenshot = true;
              });
            } catch (e) {
              if (logs.length > 100) logs.removeLast();
              logs.insert(0, "IMG ERR: $e");
            }
          }
          // Other messages
          else {
            if (logs.length > 100) logs.removeLast();
            logs.insert(0, "CMD: $data");
          }
        } catch (e) {
          if (logs.length > 100) logs.removeLast();
          logs.insert(0, "CMD: $data");
        }
      }, onError: (err) {
        logs.insert(0, "ERROR: Connection failed ($err)");
        _handleFailure();
      }, onDone: () {
        logs.insert(0, "SYSTEM: Connection closed by host");
        _handleFailure();
      });
    } catch (e) {
      logs.insert(0, "ERROR: Setup error ($e)");
      _handleFailure();
    }
  }

  void _sendAdbCommand(String action, Map<String, dynamic> params) {
    final command = {
      "type": "adb_command",
      "action": action,
      "params": params,
      "timestamp": DateTime.now().millisecondsSinceEpoch ~/ 1000
    };
    channel.sink.add(jsonEncode(command));
    setState(() {
      _commandHistory.insert(0, command);
      if (_commandHistory.length > 50) _commandHistory.removeLast();
      if (logs.length > 100) logs.removeLast();
      logs.insert(0, "SENT: $action ${params.toString()}");
    });
  }

  void _handleFailure() {
    _isConnecting = false;
    _retryCount++;
    
    if (_retryCount >= 3) {
      logs.insert(0, "SYSTEM: Multi-failure. Starting Auto-Scan...");
      _discoverService();
    } else {
      _scheduleReconnect();
    }
  }

  void _scheduleReconnect() {
    setState(() => status = "OFFLINE (RETRYING...)");
    _reconnectTimer?.cancel();
    _reconnectTimer = Timer(const Duration(seconds: 5), () => _connect());
  }

  Future<void> _discoverService() async {
    setState(() => status = "SCANNING...");
    logs.insert(0, "SCAN: Searching for TITAN Core...");
    
    try {
      final discovery = await startDiscovery('_jack-relay._tcp');
      
      Timer(const Duration(seconds: 15), () {
        stopDiscovery(discovery);
        if (status == "SCANNING...") {
           setState(() => status = "SCAN_TIMEOUT");
           logs.insert(0, "SCAN: No services found. Check Firewall.");
           _scheduleReconnect();
        }
      });

      discovery.addListener(() {
        if (discovery.services.isNotEmpty) {
          final service = discovery.services.first;
          final host = service.host;
          final port = service.port ?? 8001;
          
          if (host != null) {
            logs.insert(0, "SCAN: Found core at $host:$port");
            setState(() {
              relayUrl = "$host:$port";
              _retryCount = 0;
              _connect();
            });
            stopDiscovery(discovery);
          }
        }
      });
    } catch (e) {
      logs.insert(0, "SCAN ERROR: $e");
      _scheduleReconnect();
    }
  }

  void sendCommand(String cmd) {
    try {
      channel.sink.add(cmd);
      setState(() {
        if (logs.length > 100) logs.removeLast();
        logs.insert(0, "SENT: $cmd");
      });
    } catch (e) {
      setState(() => status = "DISCONNECTED");
    }
  }

  void _pressKey(String key) {
    _sendAdbCommand("key", {"key": key});
  }

  void _launchApp(String package) {
    _sendAdbCommand("launch", {"package": package});
  }

  Widget _buildCommandPad() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text("DEVICE CONTROLS", style: TextStyle(color: Colors.cyanAccent, fontSize: 10, letterSpacing: 2, fontWeight: FontWeight.bold)),
        const SizedBox(height: 8),
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceAround,
          children: [
            ElevatedButton(
              onPressed: () => _pressKey('BACK'),
              style: ElevatedButton.styleFrom(backgroundColor: Colors.blueGrey),
              child: const Text('BACK', style: TextStyle(fontSize: 10)),
            ),
            ElevatedButton(
              onPressed: () => _pressKey('HOME'),
              style: ElevatedButton.styleFrom(backgroundColor: Colors.blueGrey),
              child: const Text('HOME', style: TextStyle(fontSize: 10)),
            ),
            ElevatedButton(
              onPressed: () => _pressKey('ENTER'),
              style: ElevatedButton.styleFrom(backgroundColor: Colors.blueGrey),
              child: const Text('ENTER', style: TextStyle(fontSize: 10)),
            ),
          ],
        ),
        const SizedBox(height: 8),
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceAround,
          children: [
            ElevatedButton(
              onPressed: () => _launchApp('com.android.chrome'),
              child: const Text('Chrome'),
            ),
            ElevatedButton(
              onPressed: () => _launchApp('com.whatsapp'),
              child: const Text('WhatsApp'),
            ),
            ElevatedButton(
              onPressed: () => _launchApp('com.google.android.youtube'),
              child: const Text('YouTube'),
            ),
          ],
        ),
      ],
    );
  }

  Widget _buildCommandFeed() {
    if (_commandHistory.isEmpty) return const SizedBox.shrink();
    return Container(
      height: 120,
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.05),
        borderRadius: BorderRadius.circular(8),
      ),
      child: ListView.builder(
        itemCount: _commandHistory.length,
        itemBuilder: (context, i) {
          final cmd = _commandHistory[i];
          final action = cmd['action'] ?? '';
          final params = cmd['params'] != null ? cmd['params'].toString() : '';
          return ListTile(
            dense: true,
            visualDensity: VisualDensity.compact,
            title: Text("$action $params", style: const TextStyle(fontSize: 11, color: Colors.white70)),
          );
        },
      ),
    );
  }

  Widget _buildScreenshotView() {
    if (_lastScreenshot == null) return const SizedBox.shrink();
    return Column(
      children: [
        const Text("DEVICE SCREEN", style: TextStyle(color: Colors.white38, fontSize: 10)),
        const SizedBox(height: 8),
        Container(
          width: 320,
          height: 200,
          decoration: BoxDecoration(
            border: Border.all(color: Colors.cyanAccent),
            borderRadius: BorderRadius.circular(8),
          ),
          child: Image.memory(_lastScreenshot!, gaplessPlayback: true, fit: BoxFit.contain),
        ),
        TextButton(
          onPressed: () => setState(() => _showScreenshot = !_showScreenshot),
          child: Text(_showScreenshot ? 'Hide Screenshot' : 'Show Screenshot'),
        ),
      ],
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.black,
      body: Stack(
        children: [
          Container(
            decoration: const BoxDecoration(
              gradient: LinearGradient(
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
                colors: [Color(0xFF020610), Color(0xFF0A1931), Color(0xFF020610)],
              ),
            ),
          ),
          SafeArea(
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 24.0, vertical: 16.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  _buildTopNav(),
                  const SizedBox(height: 24),
                  _buildSystemStatus(),
                  const SizedBox(height: 32),
                  const Text("NEURAL ACTIONS", style: TextStyle(color: Colors.cyanAccent, fontSize: 10, letterSpacing: 2, fontWeight: FontWeight.bold)),
                  const SizedBox(height: 12),
                  _buildActionGrid(),
                  const SizedBox(height: 32),
                  const Text("LIVE TELEMETRY", style: TextStyle(color: Colors.white38, fontSize: 10, letterSpacing: 2)),
                  const SizedBox(height: 12),
                  _buildLogFeed(),
                  const SizedBox(height: 20),
                  _buildCommandPad(),
                  const SizedBox(height: 20),
                  _buildCommandFeed(),
                  const SizedBox(height: 20),
                  _buildScreenshotView(),
                  const SizedBox(height: 20),
                  _buildMainInterface(),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildTopNav() {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text("J.A.C.K.", style: TextStyle(fontSize: 28, fontWeight: FontWeight.w900, letterSpacing: 6, color: Colors.white)),
            Text("TITAN PROTOCOL // $status", style: TextStyle(color: _getStatusColor(), fontSize: 10, fontWeight: FontWeight.bold, letterSpacing: 1.5)),
          ],
        ),
        Row(
          children: [
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                border: Border.all(color: Colors.white10),
              ),
              child: IconButton(
                icon: const Icon(Icons.qr_code_scanner, color: Colors.cyanAccent),
                onPressed: _showScanner,
              ),
            ),
            const SizedBox(width: 12),
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                border: Border.all(color: Colors.white10),
                boxShadow: [
                  BoxShadow(color: Colors.cyanAccent.withValues(alpha: 0.05), blurRadius: 10, spreadRadius: 2)
                ]
              ),
              child: const Icon(Icons.settings_outlined, color: Colors.white70, size: 24),
            ),
          ],
        ),
      ],
    );
  }

  void _showScanner() {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.black,
      builder: (context) => SizedBox(
        height: MediaQuery.of(context).size.height * 0.8,
        child: Column(
          children: [
            const Padding(
              padding: EdgeInsets.all(24.0),
              child: Text("SCAN NEURAL LINK", style: TextStyle(color: Colors.cyanAccent, fontWeight: FontWeight.bold, letterSpacing: 2)),
            ),
            Expanded(
              child: MobileScanner(
                onDetect: (capture) {
                  final List<Barcode> barcodes = capture.barcodes;
                  for (final barcode in barcodes) {
                    final String? code = barcode.rawValue;
                    if (code != null && code.startsWith("jack_link:")) {
                      _handlePairing(code);
                      Navigator.pop(context);
                      break;
                    }
                  }
                },
              ),
            ),
            Padding(
              padding: const EdgeInsets.all(24.0),
              child: TextButton(
                onPressed: () => Navigator.pop(context),
                child: const Text("CANCEL", style: TextStyle(color: Colors.white38)),
              ),
            ),
          ],
        ),
      ),
    );
  }

  void _handlePairing(String code) {
    try {
      final b64 = code.split(":")[1];
      final decoded = utf8.decode(base64.decode(b64));
      final data = jsonDecode(decoded);
      
      setState(() {
        relayUrl = "${data['ip']}:${data['port']}";
        logs.insert(0, "SYSTEM: Paired with ${data['name']} via QR");
        _connect();
      });
    } catch (e) {
      logs.insert(0, "ERROR: Pairing failed ($e)");
    }
  }

  Color _getStatusColor() {
    switch (status) {
      case "ONLINE": return Colors.greenAccent;
      case "CONNECTING...": return Colors.orangeAccent;
      default: return Colors.redAccent;
    }
  }

  Widget _buildSystemStatus() {
    return Row(
      children: [
        Expanded(child: _metricCard("NEURAL LOAD", cpu, Colors.cyanAccent)),
        const SizedBox(width: 16),
        Expanded(child: _metricCard("MEMORY SWARM", ram, Colors.purpleAccent)),
      ],
    );
  }

  Widget _metricCard(String label, double value, Color color) {
    return ClipRRect(
      borderRadius: BorderRadius.circular(20),
      child: BackdropFilter(
        filter: ImageFilter.blur(sigmaX: 15, sigmaY: 15),
        child: Container(
          padding: const EdgeInsets.all(20),
          decoration: BoxDecoration(
            color: Colors.white.withValues(alpha: 0.03),
            border: Border.all(color: Colors.white.withValues(alpha: 0.05)),
            borderRadius: BorderRadius.circular(20),
          ),
          child: Column(
            children: [
              Text(label, style: const TextStyle(color: Colors.white38, fontSize: 9, letterSpacing: 1)),
              const SizedBox(height: 16),
              Stack(
                alignment: Alignment.center,
                children: [
                  SizedBox(
                    width: 60, height: 60,
                    child: CircularProgressIndicator(
                      value: value / 100,
                      color: color,
                      backgroundColor: color.withValues(alpha: 0.1),
                      strokeWidth: 4,
                    ),
                  ),
                  Text("${value.toInt()}%", style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
                ],
              )
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildActionGrid() {
    return SingleChildScrollView(
      scrollDirection: Axis.horizontal,
      physics: const BouncingScrollPhysics(),
      child: Row(
        children: [
          _actionTile("CORE_SYNC", Icons.sync, () => _connect()),
          _actionTile("AUTO_SCAN", Icons.radar, () => _discoverService()),
          _actionTile("BROWSER_X", Icons.public, () => sendCommand("open chrome")),
          _actionTile("CLEAN_SWEEP", Icons.auto_fix_high, () => sendCommand("clean junk")),
        ],
      ),
    );
  }

  Widget _actionTile(String label, IconData icon, VoidCallback tap) {
    return GestureDetector(
      onTap: tap,
      child: Container(
        margin: const EdgeInsets.only(right: 12),
        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
        decoration: BoxDecoration(
          color: Colors.white.withValues(alpha: 0.03),
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: Colors.white.withValues(alpha: 0.05)),
        ),
        child: Row(
          children: [
            Icon(icon, size: 16, color: Colors.cyanAccent),
            const SizedBox(width: 10),
            Text(label, style: const TextStyle(fontSize: 10, fontWeight: FontWeight.bold, letterSpacing: 1)),
          ],
        ),
      ),
    );
  }

  Widget _buildLogFeed() {
    return Expanded(
      child: Container(
        width: double.infinity,
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: Colors.black.withValues(alpha: 0.4),
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: Colors.white10),
        ),
        child: ListView.builder(
          physics: const BouncingScrollPhysics(),
          itemCount: logs.length,
          itemBuilder: (context, index) {
            final log = logs[index];
            bool isSent = log.startsWith("SENT:");
            return Padding(
              padding: const EdgeInsets.symmetric(vertical: 4.0),
              child: Text(
                log,
                style: TextStyle(
                  fontFamily: "monospace",
                  fontSize: 10,
                  color: isSent ? Colors.cyanAccent : Colors.white70,
                ),
              ),
            );
          },
        ),
      ),
    );
  }

  Widget _buildMainInterface() {
    return Center(
      child: GestureDetector(
        onTap: () => setState(() => isListening = !isListening),
        child: AnimatedBuilder(
          animation: _animationController,
          builder: (context, child) {
            return Container(
              padding: const EdgeInsets.all(24),
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                gradient: LinearGradient(
                  colors: isListening 
                    ? [Colors.redAccent, Colors.red.shade900] 
                    : [Colors.cyanAccent, Colors.blue.shade900],
                ),
                boxShadow: [
                  BoxShadow(
                    color: (isListening ? Colors.redAccent : Colors.cyanAccent).withValues(alpha: 0.3),
                    blurRadius: 20 + (_animationController.value * 20),
                    spreadRadius: 5 + (_animationController.value * 5),
                  )
                ]
              ),
              child: Icon(isListening ? Icons.stop_rounded : Icons.mic_rounded, size: 40, color: Colors.white),
            );
          },
        ),
      ),
    );
  }

  void _showSettingsPanel() {
    final controller = TextEditingController(text: relayUrl);
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (context) => Container(
        padding: EdgeInsets.only(bottom: MediaQuery.of(context).viewInsets.bottom),
        decoration: const BoxDecoration(
          color: Color(0xFF0F172A),
          borderRadius: BorderRadius.vertical(top: Radius.circular(32)),
          boxShadow: [BoxShadow(color: Colors.black54, blurRadius: 40)],
        ),
        child: Padding(
          padding: const EdgeInsets.all(32.0),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Center(child: Container(width: 40, height: 4, decoration: BoxDecoration(color: Colors.white10, borderRadius: BorderRadius.circular(2)))),
              const SizedBox(height: 24),
              const Text("NEURAL LINK CONFIG", style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold, letterSpacing: 2)),
              const SizedBox(height: 8),
              const Text("Enter your PC's IP address and relay port (default 8001).", style: TextStyle(color: Colors.white38, fontSize: 12)),
              const SizedBox(height: 32),
              TextField(
                controller: controller,
                autofocus: true,
                style: const TextStyle(fontFamily: "monospace", color: Colors.cyanAccent),
                decoration: InputDecoration(
                  labelText: "RELAY_ENDPOINT",
                  labelStyle: const TextStyle(color: Colors.white38, fontSize: 10),
                  filled: true,
                  fillColor: Colors.white.withValues(alpha: 0.05),
                  border: OutlineInputBorder(borderRadius: BorderRadius.circular(16), borderSide: BorderSide.none),
                  prefixIcon: const Icon(Icons.lan, color: Colors.white24),
                ),
              ),
              const SizedBox(height: 24),
              SizedBox(
                width: double.infinity,
                height: 56,
                child: ElevatedButton(
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.cyanAccent,
                    foregroundColor: Colors.black,
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                    elevation: 0,
                  ),
                  onPressed: () {
                    final newUrl = controller.text.trim();
                    if (newUrl.isNotEmpty) {
                      setState(() {
                        relayUrl = newUrl;
                        _connect();
                      });
                      Navigator.pop(context);
                    }
                  },
                  child: const Text("INITIALIZE CONNECTION", style: TextStyle(fontWeight: FontWeight.bold, letterSpacing: 1)),
                ),
              ),
              const SizedBox(height: 16),
            ],
          ),
        ),
      ),
    );
  }
}
