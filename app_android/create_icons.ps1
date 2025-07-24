# Script to create basic PNG icons for Android app
# This creates simple colored squares as placeholder icons

$iconSizes = @{
    "mipmap-mdpi" = 48
    "mipmap-hdpi" = 72
    "mipmap-xhdpi" = 96
    "mipmap-xxhdpi" = 144
    "mipmap-xxxhdpi" = 192
}

# Create a simple SVG content for the icon
$svgContent = @"
<svg width="192" height="192" xmlns="http://www.w3.org/2000/svg">
  <rect width="192" height="192" fill="#2196F3"/>
  <text x="96" y="110" font-family="Arial, sans-serif" font-size="48" fill="white" text-anchor="middle" font-weight="bold">A</text>
</svg>
"@

# Save SVG file
$svgPath = "temp_icon.svg"
$svgContent | Out-File -FilePath $svgPath -Encoding UTF8

Write-Host "Created SVG icon template"

# For now, we'll create simple XML drawable icons that reference the existing drawables
foreach ($density in $iconSizes.Keys) {
    $size = $iconSizes[$density]
    $dir = "app\src\main\res\$density"
    
    if (!(Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force
    }
    
    # Create a simple XML drawable that references our vector drawable
    $xmlContent = @"
<?xml version="1.0" encoding="utf-8"?>
<layer-list xmlns:android="http://schemas.android.com/apk/res/android">
    <item android:drawable="@drawable/ic_launcher_background" />
    <item android:drawable="@drawable/ic_launcher_foreground" />
</layer-list>
"@
    
    $xmlContent | Out-File -FilePath "$dir\ic_launcher.xml" -Encoding UTF8
    $xmlContent | Out-File -FilePath "$dir\ic_launcher_round.xml" -Encoding UTF8
    
    Write-Host "Created icons for $density (${size}x${size})"
}

# Clean up
if (Test-Path $svgPath) {
    Remove-Item $svgPath
}

Write-Host "Icon creation complete!"
