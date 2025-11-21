/**
 * Unit tests for Rate Limit Tracker
 */

import rateLimitTracker from '../rateLimitTracker.js';

describe('RateLimitTracker', () => {
  beforeEach(() => {
    rateLimitTracker.resetAll();
  });

  afterEach(() => {
    rateLimitTracker.resetAll();
  });

  describe('incrementUsage', () => {
    it('should increment usage counter for provider', () => {
      rateLimitTracker.incrementUsage('groq');

      const stats = rateLimitTracker.getStats();
      expect(stats.groq.count).toBe(1);
    });

    it('should handle multiple increments', () => {
      rateLimitTracker.incrementUsage('groq');
      rateLimitTracker.incrementUsage('groq');
      rateLimitTracker.incrementUsage('groq');

      const stats = rateLimitTracker.getStats();
      expect(stats.groq.count).toBe(3);
    });

    it('should handle unknown provider gracefully', () => {
      // Should not throw
      expect(() => {
        rateLimitTracker.incrementUsage('unknown');
      }).not.toThrow();
    });
  });

  describe('getHeadroom', () => {
    it('should return 1.0 for unused provider', () => {
      const headroom = rateLimitTracker.getHeadroom('groq');
      expect(headroom).toBe(1.0);
    });

    it('should calculate headroom correctly', () => {
      // Groq has limit of 30
      for (let i = 0; i < 15; i++) {
        rateLimitTracker.incrementUsage('groq');
      }

      const headroom = rateLimitTracker.getHeadroom('groq');
      expect(headroom).toBe(0.5); // (30 - 15) / 30
    });

    it('should return 0 when limit reached', () => {
      // Groq has limit of 30
      for (let i = 0; i < 30; i++) {
        rateLimitTracker.incrementUsage('groq');
      }

      const headroom = rateLimitTracker.getHeadroom('groq');
      expect(headroom).toBe(0);
    });

    it('should not go negative even if limit exceeded', () => {
      // Groq has limit of 30
      for (let i = 0; i < 35; i++) {
        rateLimitTracker.incrementUsage('groq');
      }

      const headroom = rateLimitTracker.getHeadroom('groq');
      expect(headroom).toBeGreaterThanOrEqual(0);
    });
  });

  describe('getAllHeadroom', () => {
    it('should return headroom for all providers', () => {
      rateLimitTracker.incrementUsage('groq');
      rateLimitTracker.incrementUsage('google');

      const headroom = rateLimitTracker.getAllHeadroom();

      expect(headroom).toHaveProperty('groq');
      expect(headroom).toHaveProperty('google');
      expect(headroom).toHaveProperty('openrouter');
      expect(headroom.groq).toBeLessThan(1.0);
      expect(headroom.google).toBeLessThan(1.0);
      expect(headroom.openrouter).toBe(1.0);
    });
  });

  describe('resetIfExpired', () => {
    it('should reset counter after window expires', () => {
      jest.useFakeTimers();

      rateLimitTracker.incrementUsage('groq');
      rateLimitTracker.incrementUsage('groq');

      let stats = rateLimitTracker.getStats();
      expect(stats.groq.count).toBe(2);

      // Advance time beyond window (60 seconds)
      jest.advanceTimersByTime(61000);

      // Trigger reset check
      rateLimitTracker.getHeadroom('groq');

      stats = rateLimitTracker.getStats();
      expect(stats.groq.count).toBe(0);

      jest.useRealTimers();
    });

    it('should not reset before window expires', () => {
      jest.useFakeTimers();

      rateLimitTracker.incrementUsage('groq');

      jest.advanceTimersByTime(30000); // Only 30 seconds

      rateLimitTracker.getHeadroom('groq');

      const stats = rateLimitTracker.getStats();
      expect(stats.groq.count).toBe(1);

      jest.useRealTimers();
    });
  });

  describe('reset', () => {
    it('should reset counter for specific provider', () => {
      rateLimitTracker.incrementUsage('groq');
      rateLimitTracker.incrementUsage('google');

      rateLimitTracker.reset('groq');

      const stats = rateLimitTracker.getStats();
      expect(stats.groq.count).toBe(0);
      expect(stats.google.count).toBe(1);
    });
  });

  describe('resetAll', () => {
    it('should reset all provider counters', () => {
      rateLimitTracker.incrementUsage('groq');
      rateLimitTracker.incrementUsage('google');
      rateLimitTracker.incrementUsage('openrouter');

      rateLimitTracker.resetAll();

      const stats = rateLimitTracker.getStats();
      expect(stats.groq.count).toBe(0);
      expect(stats.google.count).toBe(0);
      expect(stats.openrouter.count).toBe(0);
    });
  });

  describe('getStats', () => {
    it('should return detailed statistics', () => {
      rateLimitTracker.incrementUsage('groq');

      const stats = rateLimitTracker.getStats();

      expect(stats.groq).toHaveProperty('count');
      expect(stats.groq).toHaveProperty('limit');
      expect(stats.groq).toHaveProperty('headroom');
      expect(stats.groq).toHaveProperty('headroomPercent');
      expect(stats.groq).toHaveProperty('window');
      expect(stats.groq).toHaveProperty('timeUntilReset');
      expect(stats.groq).toHaveProperty('lastReset');
    });

    it('should calculate headroom percentage correctly', () => {
      // Groq limit is 30
      for (let i = 0; i < 15; i++) {
        rateLimitTracker.incrementUsage('groq');
      }

      const stats = rateLimitTracker.getStats();
      expect(stats.groq.headroomPercent).toBe(50); // 50%
    });
  });

  describe('updateLimit', () => {
    it('should update rate limit for provider', () => {
      rateLimitTracker.updateLimit('groq', 50, 120000);

      const stats = rateLimitTracker.getStats();
      expect(stats.groq.limit).toBe(50);
      expect(stats.groq.window).toBe(120000);
    });

    it('should reset counter when updating limit', () => {
      rateLimitTracker.incrementUsage('groq');
      rateLimitTracker.updateLimit('groq', 50, 60000);

      const stats = rateLimitTracker.getStats();
      expect(stats.groq.count).toBe(0);
    });
  });
});
