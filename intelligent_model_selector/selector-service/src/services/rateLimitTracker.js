/**
 * Rate Limit Tracker - Track API usage and calculate headroom
 */

import { RATE_LIMIT_DEFAULTS } from '../config/constants.js';

class RateLimitTracker {
  constructor() {
    this.counters = {};

    // Initialize counters for each provider
    Object.keys(RATE_LIMIT_DEFAULTS).forEach(provider => {
      this.counters[provider] = {
        count: 0,
        limit: RATE_LIMIT_DEFAULTS[provider].limit,
        window: RATE_LIMIT_DEFAULTS[provider].window,
        lastReset: Date.now()
      };
    });

    // Auto-reset counters periodically
    this.startAutoReset();
  }

  /**
   * Increment usage counter for a provider
   * @param {string} provider - Provider name
   */
  incrementUsage(provider) {
    if (!this.counters[provider]) {
      console.warn(`Unknown provider: ${provider}`);
      return;
    }

    // Reset if window expired
    this.resetIfExpired(provider);

    this.counters[provider].count++;
  }

  /**
   * Get headroom for a provider (available capacity)
   * @param {string} provider - Provider name
   * @returns {number} Headroom ratio (0.0-1.0)
   */
  getHeadroom(provider) {
    if (!this.counters[provider]) {
      return 0;
    }

    // Reset if window expired
    this.resetIfExpired(provider);

    const { count, limit } = this.counters[provider];
    return Math.max(0, (limit - count) / limit);
  }

  /**
   * Get headroom for all providers
   * @returns {Object} Map of provider to headroom
   */
  getAllHeadroom() {
    const headroom = {};

    Object.keys(this.counters).forEach(provider => {
      headroom[provider] = this.getHeadroom(provider);
    });

    return headroom;
  }

  /**
   * Reset counter if window has expired
   * @param {string} provider - Provider name
   */
  resetIfExpired(provider) {
    const counter = this.counters[provider];
    const now = Date.now();
    const elapsed = now - counter.lastReset;

    if (elapsed >= counter.window) {
      counter.count = 0;
      counter.lastReset = now;
    }
  }

  /**
   * Manually reset counter for a provider
   * @param {string} provider - Provider name
   */
  reset(provider) {
    if (!this.counters[provider]) {
      return;
    }

    this.counters[provider].count = 0;
    this.counters[provider].lastReset = Date.now();
  }

  /**
   * Reset all counters
   */
  resetAll() {
    Object.keys(this.counters).forEach(provider => {
      this.reset(provider);
    });
  }

  /**
   * Start automatic counter reset timer
   */
  startAutoReset() {
    // Check every 10 seconds for expired windows
    this.autoResetInterval = setInterval(() => {
      Object.keys(this.counters).forEach(provider => {
        this.resetIfExpired(provider);
      });
    }, 10000);
  }

  /**
   * Stop automatic counter reset timer
   */
  stopAutoReset() {
    if (this.autoResetInterval) {
      clearInterval(this.autoResetInterval);
    }
  }

  /**
   * Get current stats for all providers
   * @returns {Object} Stats object
   */
  getStats() {
    const stats = {};

    Object.keys(this.counters).forEach(provider => {
      const counter = this.counters[provider];
      const headroom = this.getHeadroom(provider);
      const elapsed = Date.now() - counter.lastReset;
      const timeUntilReset = Math.max(0, counter.window - elapsed);

      stats[provider] = {
        count: counter.count,
        limit: counter.limit,
        headroom,
        headroomPercent: Math.round(headroom * 100),
        window: counter.window,
        timeUntilReset,
        lastReset: new Date(counter.lastReset).toISOString()
      };
    });

    return stats;
  }

  /**
   * Update rate limit for a provider (if provider changes limits)
   * @param {string} provider - Provider name
   * @param {number} newLimit - New rate limit
   * @param {number} newWindow - New window in milliseconds
   */
  updateLimit(provider, newLimit, newWindow) {
    if (!this.counters[provider]) {
      console.warn(`Unknown provider: ${provider}`);
      return;
    }

    this.counters[provider].limit = newLimit;
    this.counters[provider].window = newWindow;
    this.reset(provider);
  }
}

// Singleton instance
const rateLimitTracker = new RateLimitTracker();

export default rateLimitTracker;
