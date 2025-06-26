import 'dart:convert';
import 'package:shared_preferences/shared_preferences.dart';

class CacheService {
  static final CacheService _instance = CacheService._internal();
  factory CacheService() => _instance;
  CacheService._internal();

  // In-memory cache for faster access during app session
  final Map<String, CacheEntry> _memoryCache = {};

  // Cache duration constants (in minutes)
  static const int accountsCacheDuration = 60;
  static const int envelopesCacheDuration = 30;
  static const int payeesCacheDuration = 15;

  Future<void> cacheAccounts(String budgetId, List<Map<String, String>> accounts) async {
    await _cacheData('accounts_$budgetId', accounts, accountsCacheDuration);
  }

  Future<void> cacheEnvelopes(String budgetId, List<Map<String, dynamic>> envelopes, List<Map<String, dynamic>> categories) async {
    final data = {
      'envelopes': envelopes,
      'categories': categories,
    };
    await _cacheData('envelopes_$budgetId', data, envelopesCacheDuration);
  }

  Future<void> cachePayees(String budgetId, List<Map<String, String>> payees) async {
    await _cacheData('payees_$budgetId', payees, payeesCacheDuration);
  }

  Future<List<Map<String, String>>?> getCachedAccounts(String budgetId) async {
    final data = await _getCachedData('accounts_$budgetId');
    if (data != null && data is List) {
      return List<Map<String, String>>.from(
        data.map((item) => Map<String, String>.from(item))
      );
    }
    return null;
  }

  Future<Map<String, dynamic>?> getCachedEnvelopes(String budgetId) async {
    final data = await _getCachedData('envelopes_$budgetId');
    if (data != null && data is Map) {
      return {
        'envelopes': List<Map<String, dynamic>>.from(data['envelopes'] ?? []),
        'categories': List<Map<String, dynamic>>.from(data['categories'] ?? []),
      };
    }
    return null;
  }

  Future<List<Map<String, String>>?> getCachedPayees(String budgetId) async {
    final data = await _getCachedData('payees_$budgetId');
    if (data != null && data is List) {
      return List<Map<String, String>>.from(
        data.map((item) => Map<String, String>.from(item))
      );
    }
    return null;
  }

  // Manual cache invalidation methods
  Future<void> invalidateAccounts(String budgetId) async {
    await _invalidateCache('accounts_$budgetId');
  }

  Future<void> invalidateEnvelopes(String budgetId) async {
    await _invalidateCache('envelopes_$budgetId');
  }

  Future<void> invalidatePayees(String budgetId) async {
    await _invalidateCache('payees_$budgetId');
  }

  Future<void> invalidateAllCache(String budgetId) async {
    await invalidateAccounts(budgetId);
    await invalidateEnvelopes(budgetId);
    await invalidatePayees(budgetId);
  }

  // Private helper methods
  Future<void> _cacheData(String key, dynamic data, int durationMinutes) async {
    final now = DateTime.now().millisecondsSinceEpoch;
    final expiryTime = now + (durationMinutes * 60 * 1000);
    
    final cacheEntry = CacheEntry(
      data: data,
      timestamp: now,
      expiryTime: expiryTime,
    );

    // Store in memory cache
    _memoryCache[key] = cacheEntry;

    // Store in persistent cache
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(key, json.encode(cacheEntry.toJson()));
  }

  Future<dynamic> _getCachedData(String key) async {
    final now = DateTime.now().millisecondsSinceEpoch;

    // Check memory cache first
    if (_memoryCache.containsKey(key)) {
      final entry = _memoryCache[key]!;
      if (now < entry.expiryTime) {
        return entry.data;
      } else {
        // Expired, remove from memory
        _memoryCache.remove(key);
      }
    }

    // Check persistent cache
    final prefs = await SharedPreferences.getInstance();
    final cachedString = prefs.getString(key);
    
    if (cachedString != null) {
      try {
        final cachedJson = json.decode(cachedString);
        final entry = CacheEntry.fromJson(cachedJson);
        
        if (now < entry.expiryTime) {
          // Valid cache, store in memory for faster access
          _memoryCache[key] = entry;
          return entry.data;
        } else {
          // Expired, remove from persistent storage
          await prefs.remove(key);
        }
      } catch (e) {
        // Invalid cache data, remove it
        await prefs.remove(key);
      }
    }

    return null;
  }

  Future<void> _invalidateCache(String key) async {
    // Remove from memory cache
    _memoryCache.remove(key);
    
    // Remove from persistent cache
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(key);
  }

  // Check if cache exists and is valid
  Future<bool> isCacheValid(String key) async {
    final now = DateTime.now().millisecondsSinceEpoch;
    
    // Check memory cache first
    if (_memoryCache.containsKey(key)) {
      return now < _memoryCache[key]!.expiryTime;
    }

    // Check persistent cache
    final prefs = await SharedPreferences.getInstance();
    final cachedString = prefs.getString(key);
    
    if (cachedString != null) {
      try {
        final cachedJson = json.decode(cachedString);
        final entry = CacheEntry.fromJson(cachedJson);
        return now < entry.expiryTime;
      } catch (e) {
        return false;
      }
    }

    return false;
  }

  // Get cache info for debugging
  Future<Map<String, dynamic>> getCacheInfo(String budgetId) async {
    return {
      'accounts_valid': await isCacheValid('accounts_$budgetId'),
      'envelopes_valid': await isCacheValid('envelopes_$budgetId'),
      'payees_valid': await isCacheValid('payees_$budgetId'),
      'memory_cache_size': _memoryCache.length,
    };
  }
}

class CacheEntry {
  final dynamic data;
  final int timestamp;
  final int expiryTime;

  CacheEntry({
    required this.data,
    required this.timestamp,
    required this.expiryTime,
  });

  Map<String, dynamic> toJson() {
    return {
      'data': data,
      'timestamp': timestamp,
      'expiryTime': expiryTime,
    };
  }

  factory CacheEntry.fromJson(Map<String, dynamic> json) {
    return CacheEntry(
      data: json['data'],
      timestamp: json['timestamp'],
      expiryTime: json['expiryTime'],
    );
  }
}
