allprojects {
    repositories {
        google()
        mavenCentral()
    }
}

val newBuildDir: Directory =
    rootProject.layout.buildDirectory
        .dir("../../build")
        .get()
rootProject.layout.buildDirectory.value(newBuildDir)

subprojects {
    val newSubprojectBuildDir: Directory = newBuildDir.dir(project.name)
    project.layout.buildDirectory.value(newSubprojectBuildDir)
}

subprojects {
    project.evaluationDependsOn(":app")
}

subprojects {
    // Inject namespace and clean manifests for AGP 8+ compatibility
    plugins.withType<com.android.build.gradle.BasePlugin> {
        val android = project.extensions.getByName("android") as com.android.build.gradle.BaseExtension
        
        // Inject namespace if missing
        if (android.namespace == null) {
            android.namespace = "jack.mobile.plugin.${project.name.replace("-", "_")}"
        }
        
        // Aggressively strip 'package' attribute from manifest to resolve AGP 8+ conflicts
        project.tasks.matching { 
            val taskName = it.name.lowercase()
            taskName.contains("manifest") && (taskName.contains("process") || taskName.contains("merge"))
        }.configureEach {
            doFirst {
                val manifestFile = project.file("src/main/AndroidManifest.xml")
                if (manifestFile.exists()) {
                    val content = manifestFile.readText()
                    if (content.contains("package=")) {
                        val newContent = content.replace(Regex("""package\s*=\s*"[^"]*""""), "")
                        manifestFile.writeText(newContent)
                        println("TITAN_FIX: Sanitized manifest for ${project.name}")
                    }
                }
            }
        }
    }
}

tasks.register<Delete>("clean") {
    delete(rootProject.layout.buildDirectory)
}
