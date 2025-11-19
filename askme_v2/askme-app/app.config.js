import 'dotenv/config';

export default {
  expo: {
    name: "AskMe - Ask Any LLM",
    slug: "askme",
    version: "1.0.0",
    orientation: "portrait",
    icon: "./assets/icon.png",
    userInterfaceStyle: "light",
    splash: {
      image: "./assets/splash.png",
      resizeMode: "contain",
      backgroundColor: "#ffffff"
    },
    assetBundlePatterns: [
      "**/*"
    ],
    ios: {
      bundleIdentifier: "com.askme.app"
    },
    android: {
      adaptiveIcon: {
        foregroundImage: "./assets/adaptive-icon.png",
        backgroundColor: "#ffffff"
      },
      package: "com.askme.app",
      permissions: [
        "android.permission.INTERNET",
        "android.permission.ACCESS_NETWORK_STATE"
      ]
    },
    web: {
      favicon: "./assets/favicon.png"
    },
    extra: {
      eas: {
        projectId: "34f0b11c-4b05-45a5-b3ff-4f826a48e7d5"
      },
      // Load environment variables
      backendUrl: process.env.EXPO_PUBLIC_BACKEND_URL || 'https://askme-v2.onrender.com',
      apiTimeout: process.env.EXPO_PUBLIC_API_TIMEOUT || '30000',
      appVersion: process.env.EXPO_PUBLIC_APP_VERSION || '1.0.0',
      cacheTtlDays: process.env.EXPO_PUBLIC_CACHE_TTL_DAYS || '7',
      offlineQueueMaxSize: process.env.EXPO_PUBLIC_OFFLINE_QUEUE_MAX_SIZE || '10',
      cacheSizeLimitMb: process.env.EXPO_PUBLIC_CACHE_SIZE_LIMIT_MB || '50',
      debug: process.env.EXPO_PUBLIC_DEBUG || 'false',
    }
  }
};
