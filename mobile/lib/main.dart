import 'dart:convert';
import 'dart:ui';
import 'package:flutter/material.dart';
import 'package:web_socket_channel/web_socket_channel.dart';

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
  String relayUrl = '192.168.0.14:8001'; // Updated to match PC IP
  late WebSocketChannel channel;
  late AnimationController _animationController;
  
  double cpu = 0.0;
  double ram = 0.0;
  String status = "OFFLINE";
  List<String> logs = [];
  bool isListening = false;

  @override
  void initState() {
    super.initState();
    _animationController = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 2),
    )..repeat(reverse: true);
    _connect();
  }

  @override
  void dispose() {
    _animationController.dispose();
    channel.sink.close();
    super.dispose();
  }

  void _connect() {
    setState(() => status = "CONNECTING...");
    try {
      channel = WebSocketChannel.connect(
        Uri.parse('ws://$relayUrl/ws/jack_secure_neural_link_2026'),
      );
      channel.stream.listen((data) {
        try {
          final jsonData = jsonDecode(data);
          setState(() {
            cpu = (jsonData["cpu"] ?? 0.0).toDouble();
            ram = (jsonData["ram"] ?? 0.0).toDouble();
            status = "ONLINE";
            if (logs.length > 100) logs.removeLast();
            logs.insert(0, jsonData.toString());
          });
        } catch (e) {
          if (logs.length > 100) logs.removeLast();
          logs.insert(0, "CMD: $data");
        }
      }, onError: (err) {
        setState(() => status = "ERROR");
      }, onDone: () {
        setState(() => status = "OFFLINE");
      });
    } catch (e) {
      setState(() => status = "FAILED");
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
        Material(
          color: Colors.transparent,
          child: InkWell(
            borderRadius: BorderRadius.circular(30),
            onTap: _showSettingsPanel,
            child: Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                border: Border.all(color: Colors.white10),
                boxShadow: [
                  BoxShadow(color: Colors.cyanAccent.withOpacity(0.05), blurRadius: 10, spreadRadius: 2)
                ]
              ),
              child: const Icon(Icons.settings_outlined, color: Colors.white70, size: 24),
            ),
          ),
        ),
      ],
    );
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
            color: Colors.white.withOpacity(0.03),
            border: Border.all(color: Colors.white.withOpacity(0.05)),
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
                      backgroundColor: color.withOpacity(0.1),
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
          _actionTile("BROWSER_X", Icons.public, () => sendCommand("open chrome")),
          _actionTile("SYS_SCAN", Icons.radar, () => sendCommand("scan system")),
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
          color: Colors.white.withOpacity(0.03),
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: Colors.white.withOpacity(0.05)),
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
          color: Colors.black.withOpacity(0.4),
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
                    color: (isListening ? Colors.redAccent : Colors.cyanAccent).withOpacity(0.3),
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
                  fillColor: Colors.white.withOpacity(0.05),
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
