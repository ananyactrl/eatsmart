# EatSmartly Supabase Setup Instructions

## 🔥 Firebase + Supabase Integration Complete!

Your EatSmartly app now has a powerful dual-database architecture:
- **Firebase Auth**: Handles authentication (login, signup, Google sign-in, biometric)
- **Supabase**: Stores user profiles, meal history, and app data

## 📱 **Current Authentication Flow**

1. **Sign Up/Login** → Firebase authenticates the user
2. **Profile Setup** → Data saved to Supabase with Firebase User ID as key
3. **Stay Logged In** → Firebase persistence + Supabase profile check
4. **App Usage** → All user data stored in Supabase, linked to Firebase UID

## 🔧 **Setup Required**

### **1. Create Supabase Project**
1. Go to https://supabase.com
2. Create a new project
3. Note your **Project URL** and **Anon Key**

### **2. Run Database Schema**
1. In Supabase Dashboard → SQL Editor
2. Copy and paste the entire content of `SUPABASE_COMPLETE_SCHEMA.sql`
3. Click Run
4. Should see: "EatSmartly Supabase database schema created successfully! 🎉"

### **3. Update Flutter App Configuration**

Open `lib/main.dart` and replace:

```dart
// Initialize Supabase
await SupabaseService.initialize(
  url: 'https://your-supabase-url.supabase.co',        // ← Replace this
  anonKey: 'your-supabase-anon-key',                   // ← Replace this
);
```

**With your actual values:**

```dart
await SupabaseService.initialize(
  url: 'https://xxxxxxxxxxx.supabase.co',              // Your project URL
  anonKey: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...', // Your anon key
);
```

### **4. Add SHA-1 Fingerprint to Firebase (if not done)**
Add this SHA-1 to Firebase Console for Google Sign-In:
```
B1:56:1E:A4:CD:0C:2D:52:5B:E6:ED:C6:30:CC:50:54:1D:43:3C:6C
```

## 🗃️ **Database Structure**

### **Tables Created:**
- `users` - Firebase user sync data
- `user_profiles` - Complete health profiles with BMR/TDEE calculations
- `meal_history` - AI meal planning history
- `food_scans` - Barcode scan results
- `health_conditions` - Reference data for health conditions
- `allergens` - Reference data for allergen management

### **Features Enabled:**
- ✅ **Row Level Security (RLS)** - Users can only access their own data
- ✅ **Real-time subscriptions** - Apps update when data changes
- ✅ **Automatic timestamps** - Created/updated tracking
- ✅ **JSONB storage** - Flexible profile data structure
- ✅ **Performance indexes** - Fast queries on user data

## 🚀 **Ready to Test!**

### **Complete Flow:**
1. **Run**: `flutter pub get && flutter run`
2. **Sign Up** → Creates Firebase user + Supabase entry
3. **Complete Profile** → Saves to Supabase with calculated nutrition targets
4. **Use App** → All data persists in Supabase
5. **Stay Logged In** → Firebase handles authentication persistence

### **Data Flow:**
- **Authentication**: Firebase Auth → `users` table (auto-synced)
- **Health Profile**: Comprehensive form → `user_profiles` table (JSONB)
- **Meal Planning**: AI responses → `meal_history` table
- **Food Scanning**: Barcode results → `food_scans` table

## 💾 **User Data Persistence**

- ✅ **Login State**: Firebase keeps users logged in across app restarts
- ✅ **Profile Data**: Stored in Supabase, never lost
- ✅ **Meal History**: All AI interactions saved
- ✅ **Scan History**: All barcode scans tracked
- ✅ **Cross-Device**: Same account, same data everywhere

## 🛡️ **Security Features**

- **Firebase Security Rules**: Control authentication
- **Supabase RLS**: Users only see their own data
- **Encrypted Transit**: All data encrypted in transit
- **Type Safety**: Strong typing for all database operations
- **Audit Trail**: Complete timestamp tracking

## 🔄 **Offline Support**

- **Authentication**: Firebase handles offline authentication
- **Profile Cache**: Local storage backup for quick access
- **Auto-Sync**: Data syncs when connection restored

Your app now has **enterprise-grade data architecture** with complete user persistence! 🎉