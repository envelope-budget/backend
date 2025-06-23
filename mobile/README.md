# Mobile App

This directory contains the Flutter mobile application that can be compiled for both iOS and Android platforms.

## Overview

The mobile app is built using Flutter, Google's UI toolkit for building natively compiled applications from a single
codebase. This means we can maintain one codebase that deploys to both iOS and Android devices.

## Getting Started

1. Ensure you have Flutter installed on your development machine
2. Clone this repository
3. Run `flutter pub get` to install dependencies
4. Use `flutter run` to start the app in debug mode

## Building for Production

### Android

- Run `flutter build apk` for an Android APK
- Run `flutter build appbundle` for Android App Bundle

### iOS

- Run `flutter build ios` for iOS archive
- Use Xcode to build and sign the final IPA
