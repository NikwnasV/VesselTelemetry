# Στάδιο 1: Compile με Maven
FROM maven:3.9-eclipse-temurin-21-alpine AS build
WORKDIR /app
COPY pom.xml .
COPY src ./src
RUN mvn clean package

# Στάδιο 2: Τελικό ελαφρύ container
FROM eclipse-temurin:21-jre-alpine
WORKDIR /app
# Αντιγραφή του JAR και του φακέλου με το HTML
COPY --from=build /app/target/edge-api-1.0-SNAPSHOT.jar ./app.jar
COPY public ./public
EXPOSE 8000
CMD ["java", "-jar", "app.jar"]
