#!/bin/bash
# Builds the Krews workflow and runs it on google with the given configuration
set -e

./gradlew clean shadowJar
for JAR in build/*.jar; do :; done;
java -jar ${JAR} $@
