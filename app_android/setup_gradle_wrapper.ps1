# Script to setup Gradle wrapper
$gradleWrapperUrl = "https://raw.githubusercontent.com/gradle/gradle/v8.4.0/gradle/wrapper/gradle-wrapper.jar"
$wrapperDir = "gradle\wrapper"
$wrapperJarPath = "$wrapperDir\gradle-wrapper.jar"

# Create wrapper directory if it doesn't exist
if (!(Test-Path $wrapperDir)) {
    New-Item -ItemType Directory -Path $wrapperDir -Force
}

# Download gradle wrapper jar
Write-Host "Downloading Gradle wrapper jar..."
try {
    Invoke-WebRequest -Uri $gradleWrapperUrl -OutFile $wrapperJarPath
    Write-Host "Gradle wrapper jar downloaded successfully!"
} catch {
    Write-Host "Failed to download from GitHub, trying alternative source..."
    # Try alternative source
    $altUrl = "https://services.gradle.org/distributions/gradle-8.4-wrapper.jar"
    try {
        Invoke-WebRequest -Uri $altUrl -OutFile $wrapperJarPath
        Write-Host "Gradle wrapper jar downloaded from alternative source!"
    } catch {
        Write-Host "Failed to download gradle wrapper jar. Error: $($_.Exception.Message)"
        exit 1
    }
}

Write-Host "Gradle wrapper setup complete!"
