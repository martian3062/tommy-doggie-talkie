# Dog Translator Mobile

Expo React Native app for Android APK delivery.

## Local Setup

```powershell
cd mobile
npm install
copy .env.example .env
npm start
```

For Android emulator, keep `EXPO_PUBLIC_API_BASE_URL=http://10.0.2.2:8000`.
For a physical phone, set it to your computer LAN IP, for example `http://192.168.1.20:8000`.

## Supabase

Fill these after creating the Supabase project:

```env
EXPO_PUBLIC_SUPABASE_URL=
EXPO_PUBLIC_SUPABASE_PUBLISHABLE_KEY=
EXPO_PUBLIC_SUPABASE_STORAGE_BUCKET=dog-videos
```

Without Supabase values, the app runs in local demo mode and uploads videos directly to FastAPI.

## APK

```powershell
npm install -g eas-cli
eas build -p android --profile preview
```
