import { initializeApp } from "https://www.gstatic.com/firebasejs/10.8.0/firebase-app.js";
import { getAuth, signInWithEmailAndPassword, createUserWithEmailAndPassword, GoogleAuthProvider, signInWithPopup, onAuthStateChanged, signOut } from "https://www.gstatic.com/firebasejs/10.8.0/firebase-auth.js";
import { getMessaging, getToken, onMessage } from "https://www.gstatic.com/firebasejs/10.8.0/firebase-messaging.js";

const firebaseConfig = {
    projectId: "camphe-237",
    appId: "1:206407742812:web:9d03dd72b8d2c9833bfd99",
    storageBucket: "camphe-237.firebasestorage.app",
    apiKey: "AIzaSyB6LXM-HrS3pwRotxu59xWtdW6dib0QoIA",
    authDomain: "camphe-237.firebaseapp.com",
    messagingSenderId: "206407742812",
    measurementId: "G-HD18645TPH"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
const auth = getAuth(app);

let messaging;
try {
    messaging = getMessaging(app);
} catch(e) {
    console.log("Messaging not supported in this browser environment.", e);
}

// UI Elements
const authBtn = document.getElementById('auth-btn');
const userInfo = document.getElementById('user-info');
const userEmail = document.getElementById('user-email');
const signOutBtn = document.getElementById('sign-out-btn');
const authModal = document.getElementById('auth-modal');
const closeBtn = document.querySelector('.close-btn');
const authForm = document.getElementById('auth-form');
const emailInput = document.getElementById('email');
const passwordInput = document.getElementById('password');
const googleSignInBtn = document.getElementById('google-signin-btn');
const toggleAuthModeBtn = document.getElementById('toggle-auth-mode');
const authTitle = document.getElementById('auth-title');
const emailSubmitBtn = document.getElementById('email-submit-btn');
const authError = document.getElementById('auth-error');
const enableNotificationsBtn = document.getElementById('enable-notifications-btn');

let isSignUpMode = false;

// Modal Logic
authBtn.addEventListener('click', () => {
    authModal.style.display = 'flex';
});

closeBtn.addEventListener('click', () => {
    authModal.style.display = 'none';
});

window.addEventListener('click', (e) => {
    if (e.target === authModal) {
        authModal.style.display = 'none';
    }
});

toggleAuthModeBtn.addEventListener('click', () => {
    isSignUpMode = !isSignUpMode;
    authTitle.textContent = isSignUpMode ? 'Sign Up' : 'Sign In';
    emailSubmitBtn.textContent = isSignUpMode ? 'Sign Up with Email' : 'Sign In with Email';
    toggleAuthModeBtn.textContent = isSignUpMode ? 'Already have an account? Sign in' : 'Don\'t have an account? Sign up';
});

const showError = (message) => {
    authError.textContent = message;
    authError.style.display = 'block';
};

// Auth Logic
authForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    authError.style.display = 'none';
    const email = emailInput.value;
    const password = passwordInput.value;

    try {
        if (isSignUpMode) {
            await createUserWithEmailAndPassword(auth, email, password);
        } else {
            await signInWithEmailAndPassword(auth, email, password);
        }
        authModal.style.display = 'none';
    } catch (error) {
        showError(error.message);
    }
});

googleSignInBtn.addEventListener('click', async () => {
    authError.style.display = 'none';
    const provider = new GoogleAuthProvider();
    try {
        await signInWithPopup(auth, provider);
        authModal.style.display = 'none';
    } catch (error) {
        showError(error.message);
    }
});

signOutBtn.addEventListener('click', async () => {
    await signOut(auth);
});

// Auth State Observer
onAuthStateChanged(auth, (user) => {
    if (user) {
        authBtn.style.display = 'none';
        userInfo.style.display = 'flex';
        userEmail.textContent = user.email;
        // Optionally request notification permission automatically on login
        // requestNotificationPermission();
    } else {
        authBtn.style.display = 'block';
        userInfo.style.display = 'none';
        userEmail.textContent = '';
    }
});

// Push Notifications
const requestNotificationPermission = async () => {
    try {
        const permission = await Notification.requestPermission();
        if (permission === 'granted') {
            console.log('Notification permission granted.');
            if (messaging) {
                // Add your VAPID key here later
                const currentToken = await getToken(messaging, { vapidKey: 'YOUR_VAPID_KEY_HERE' });
                if (currentToken) {
                    console.log('FCM Token:', currentToken);
                    // Send this token to your server or save it to Firestore here
                } else {
                    console.log('No registration token available. Request permission to generate one.');
                }
            }
        } else {
            console.log('Unable to get permission to notify.');
        }
    } catch (err) {
        console.error('An error occurred while retrieving token. ', err);
    }
};

enableNotificationsBtn.addEventListener('click', () => {
    requestNotificationPermission();
});

if (messaging) {
    onMessage(messaging, (payload) => {
        console.log('Message received. ', payload);
        // Customize notification here if app is in foreground
        new Notification(payload.notification.title, {
            body: payload.notification.body,
            icon: 'icon-192.png'
        });
    });
}
