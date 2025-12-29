(function() {
    'use strict';

    let sessionId = getCookie('sgnl_session');
    let pageStartTime = Date.now();
    let heartbeatInterval;
    let lastPath = window.location.pathname + window.location.search;

    function getCookie(name) {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) return parts.pop().split(';').shift();
        return null;
    }

    function setCookie(name, value, days) {
        const date = new Date();
        date.setTime(date.getTime() + (days * 24 * 60 * 60 * 1000));
        const expires = `expires=${date.toUTCString()}`;
        document.cookie = `${name}=${value};${expires};path=/`;
    }

    function generateSessionId() {
        return 'sess_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }

    function trackPageView(timeOnPage = null) {
        const data = {
            session_id: sessionId,
            path: lastPath
        };
        
        if (timeOnPage !== null) {
            data.time_on_page = timeOnPage;
        }

        send('/analytics/pageview', data);
    }

    function trackHeartbeat() {
        const data = {
            session_id: sessionId,
            path: window.location.pathname + window.location.search
        };
        send('/analytics/heartbeat', data);
    }

    function trackEvent(eventType, eventData = null) {
        const data = {
            session_id: sessionId,
            event_type: eventType
        };
        
        if (eventData) {
            data.event_data = eventData;
        }

        send('/analytics/track', data);
    }

    function send(url, data) {
        const apiBase = window.location.origin;
        
        navigator.sendBeacon(
            apiBase + url,
            JSON.stringify(data)
        );
    }

    function sendAnalyticsBeforeUnload() {
        const timeOnPage = (Date.now() - pageStartTime) / 1000;
        trackPageView(timeOnPage);
    }

    function initSession() {
        if (!sessionId) {
            sessionId = generateSessionId();
            setCookie('sgnl_session', sessionId, 90);
        }

        pageStartTime = Date.now();
        lastPath = window.location.pathname + window.location.search;

        trackPageView(0);

        heartbeatInterval = setInterval(trackHeartbeat, 30000);

        window.addEventListener('beforeunload', sendAnalyticsBeforeUnload);

        document.addEventListener('visibilitychange', function() {
            if (document.visibilityState === 'hidden') {
                sendAnalyticsBeforeUnload();
            } else if (document.visibilityState === 'visible') {
                const newPath = window.location.pathname + window.location.search;
                if (newPath !== lastPath) {
                    const timeOnPage = (Date.now() - pageStartTime) / 1000;
                    trackPageView(timeOnPage);
                    
                    lastPath = newPath;
                    pageStartTime = Date.now();
                    trackPageView(0);
                }
            }
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initSession);
    } else {
        initSession();
    }

    window.SGNLAnalytics = {
        trackEvent: trackEvent,
        getSessionId: function() { return sessionId; }
    };

})();
