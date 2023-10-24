import org.jetbrains.kotlin.gradle.tasks.KotlinCompile
import com.github.jengelman.gradle.plugins.shadow.tasks.ShadowJar

plugins {
    kotlin("jvm") version "1.7.20"
    id("application")
    id("com.github.johnrengelman.shadow") version "8.1.1"
    java
}

version = "0.10.0"

repositories {
    mavenLocal()
    jcenter()
    maven {
        name = "GitHubPackages"
        url = uri("https://maven.pkg.github.com/weng-lab/krews")
        credentials {
            username = project.findProperty("gpr.user") as String? ?: System.getenv("USERNAME")
            password = project.findProperty("gpr.key") as String? ?: System.getenv("TOKEN")
        }
    }
}

dependencies {
    implementation(kotlin("stdlib-jdk8"))
    implementation("io.krews", "krews", "0.15.2")
    implementation("io.projectreactor", "reactor-core", "3.2.6.RELEASE")
}

application {
    mainClass.set("ChromBPNetWorkflowKt")
}

tasks.withType<KotlinCompile> {
    kotlinOptions.jvmTarget = "1.8"
}

tasks.withType<ShadowJar> {
    archiveBaseName.set("base")
    archiveClassifier.set("")
    destinationDirectory.set(file("build"))
}

