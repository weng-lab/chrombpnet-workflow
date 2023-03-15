import org.jetbrains.kotlin.gradle.tasks.KotlinCompile
import com.github.jengelman.gradle.plugins.shadow.tasks.ShadowJar

plugins {
    kotlin("jvm") version "1.3.10"
    id("application")
    id("com.github.johnrengelman.shadow") version "4.0.2"
}

version = "0.9.0"

repositories {
    mavenLocal()
    jcenter()
    maven {
        url = uri("https://maven.pkg.github.com/weng-lab/krews")
        credentials {
            username = project.findProperty("gpr.user") as String? ?: System.getenv("USERNAME")
            password = project.findProperty("gpr.key") as String? ?: System.getenv("TOKEN")
        }
    }
}

dependencies {
    compile(kotlin("stdlib-jdk8"))
    compile("io.krews", "krews", "0.13.1")
}

application {
    mainClassName = "ChromBPNetWorkflowKt"
}

tasks.withType<KotlinCompile> {
    kotlinOptions.jvmTarget = "1.8"
}

tasks.withType<ShadowJar> {
    baseName = "chrombpnet"
    classifier = ""
    destinationDir = file("build")
}
