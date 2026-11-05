# Aaru Play

A responsive Flutter app starter for Android, iOS, and Web, with deployment
configuration for Firebase Hosting and GitHub Pages.

The home screen uses the six YouTube links supplied for testing: four videos
and two playlists. Selecting a card opens YouTube's embedded player; playback
still depends on the video being available in the user's region and allowing
embedding. The player dialog also links to the original YouTube URL as a
fallback. Account sign-in and offline media downloads are not connected.
Do not put private API credentials in the client app.

`icon.svg` in the project root contains the Aaru Play logo. Replace its SVG
markup to customize the app mark; Firebase and GitHub Pages builds copy it
into the published web root as the site favicon.

## Requirements

- Flutter stable SDK (with web support)
- Android Studio/Android SDK for Android builds
- macOS with Xcode for iOS builds
- Git
- Node.js/npm and Firebase CLI for Firebase deployment
- A Firebase project and a GitHub repository for publishing

## Run and test locally

```powershell
flutter pub get
flutter analyze
flutter test
flutter run -d chrome
```

Run on an Android device/emulator with `flutter run -d android`. iOS builds
must be produced on macOS with Xcode.

To preview the production web build locally, build it and copy the root logo:

```powershell
flutter build web --release --base-href "/"
Copy-Item icon.svg build\web\icon.svg -Force
python -m http.server 5455 --directory build\web
```

## Firebase Hosting

1. Install and authenticate the Firebase CLI:

   ```powershell
   npm install -g firebase-tools
   firebase login
   ```

2. From this project directory, initialize Hosting and select your Firebase
   project. Keep the existing `firebase.json`; use `build/web` as the public
   directory and do not replace the Flutter `web/index.html`.

   ```powershell
   firebase init hosting
   ```

3. Build for Firebase's root path and deploy:

   ```powershell
   flutter pub get
   flutter build web --release --base-href "/"
   firebase deploy --only hosting
   ```

   On Windows PowerShell, you can run `.\scripts\deploy_firebase.ps1` after
   logging in and initializing Hosting.

## GitHub Pages

1. Create a GitHub repository named `Aaru-Play` and push this project to its
   `main` branch.
2. The workflow at `.github/workflows/deploy.yml` runs analysis and tests,
   builds with the `/Aaru-Play/` base path, and publishes `build/web` to
   `gh-pages`.
3. In repository **Settings → Pages**, choose **Deploy from a branch**, then
   select `gh-pages` and `/(root)`.
4. The site URL is
   `https://YOUR_GITHUB_USERNAME.github.io/Aaru-Play/`.

The GitHub Pages build uses a repository subpath; Firebase uses `/`. Build
separately for each host by using the commands/workflow above.

### Initial Git setup

Create the empty GitHub repository first, then replace the username below:

```powershell
git init
git add .
git commit -m "Initial Aaru Play web app"
git branch -M main
git remote add origin https://github.com/YOUR_GITHUB_USERNAME/Aaru-Play.git
git push -u origin main
```

Never commit API keys, service-account files, or other credentials.
