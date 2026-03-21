# Keep Google ML Kit Text Recognition classes
# These language-specific recognizers are optional dependencies that may not be included
-dontwarn com.google.mlkit.vision.text.chinese.**
-dontwarn com.google.mlkit.vision.text.devanagari.**
-dontwarn com.google.mlkit.vision.text.japanese.**
-dontwarn com.google.mlkit.vision.text.korean.**

# Keep ML Kit core classes
-keep class com.google.mlkit.** { *; }
-keep interface com.google.mlkit.** { *; }

# Keep classes that are referenced via reflection
-keepclassmembers class * {
    @com.google.android.gms.common.annotation.KeepForSdk *;
}
