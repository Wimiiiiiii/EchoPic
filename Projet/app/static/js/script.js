// Importation des modules Firebase
import { initializeApp } from "https://www.gstatic.com/firebasejs/11.8.1/firebase-app.js";
import { getAuth, onAuthStateChanged, signInWithPopup, GoogleAuthProvider, signInWithEmailAndPassword, createUserWithEmailAndPassword, sendPasswordResetEmail, signOut } from "https://www.gstatic.com/firebasejs/11.8.1/firebase-auth.js";

// Configuration Firebase
const firebaseConfig = {
    apiKey: "AIzaSyDLLUxHFTuN73015L2cR6m6pYtdVKICbp8",
    authDomain: "echopic-b679d.firebaseapp.com",
    projectId: "echopic-b679d",
    storageBucket: "echopic-b679d.firebasestorage.app",
    messagingSenderId: "1003205566040",
    appId: "1:1003205566040:web:61b5cee410aa7dd0c3f42d",
    measurementId: "G-X0F64N3GC7"
  };

// Initialisation Firebase
const app = initializeApp(firebaseConfig);
const auth = getAuth(app);

// Écouteur d'état d'authentification
onAuthStateChanged(auth, user => {
    if (user) {
        showSearchInterface();
    } else {
        showAuthOptions();
    }
});

// Fonctions d'affichage
function showAuthOptions() {
    hideAllContainers();
    document.getElementById('auth-container').classList.remove('hidden');
}

function showEmailAuth() {
    hideAllContainers();
    document.getElementById('email-login-container').classList.remove('hidden');
}

function showRegister() {
    hideAllContainers();
    document.getElementById('register-container').classList.remove('hidden');
}

function showForgotPassword() {
    hideAllContainers();
    document.getElementById('forgot-password-container').classList.remove('hidden');
}

function showSearchInterface() {
    hideAllContainers();
    document.getElementById('search-container').classList.remove('hidden');
}

function hideAllContainers() {
    const containers = [
        'auth-container',
        'email-login-container',
        'register-container',
        'forgot-password-container',
        'search-container'
    ];
    containers.forEach(id => {
        document.getElementById(id)?.classList.add('hidden');
    });
}

// Fonctions d'authentification
window.loginWithGoogle = function () {
    const provider = new GoogleAuthProvider();
    signInWithPopup(auth, provider)
        .then(() => showAuthMessage("Connexion réussie!", "success"))
        .catch(error => {
            showAuthMessage("Erreur: " + error.message, "error");
            console.error(error);
        });
};

window.loginWithEmail = function () {
    const email = document.getElementById('login-email').value;
    const password = document.getElementById('login-password').value;

    if (!email || !password) {
        showAuthMessage("Veuillez remplir tous les champs", "error");
        return;
    }

    signInWithEmailAndPassword(auth, email, password)
        .then(() => showAuthMessage("Connexion réussie!", "success"))
        .catch(error => {
            showAuthMessage("Erreur: " + error.message, "error");
            console.error(error);
        });
};

window.registerWithEmail = function () {
    const email = document.getElementById('register-email').value;
    const password = document.getElementById('register-password').value;
    const confirmPassword = document.getElementById('register-confirm-password').value;

    if (!email || !password || !confirmPassword) {
        showAuthMessage("Veuillez remplir tous les champs", "error");
        return;
    }

    if (password !== confirmPassword) {
        showAuthMessage("Les mots de passe ne correspondent pas", "error");
        return;
    }

    if (password.length < 6) {
        showAuthMessage("Le mot de passe doit contenir au moins 6 caractères", "error");
        return;
    }

    createUserWithEmailAndPassword(auth, email, password)
        .then(() => showAuthMessage("Inscription réussie! Vous êtes maintenant connecté.", "success"))
        .catch(error => {
            showAuthMessage("Erreur: " + error.message, "error");
            console.error(error);
        });
};

window.sendPasswordResetEmail = function () {
    const email = document.getElementById('reset-email').value;

    if (!email) {
        showAuthMessage("Veuillez entrer votre email", "error");
        return;
    }

    sendPasswordResetEmail(auth, email)
        .then(() => showAuthMessage("Email de réinitialisation envoyé!", "success"))
        .catch(error => {
            showAuthMessage("Erreur: " + error.message, "error");
            console.error(error);
        });
};

window.logout = function () {
    signOut(auth)
        .then(() => {
            showAuthOptions();
            showAuthMessage("Déconnexion réussie", "success");
        })
        .catch(error => {
            showAuthMessage("Erreur lors de la déconnexion", "error");
            console.error(error);
        });
};

// Gestion des messages
function showAuthMessage(message, type) {
    const messageDiv = document.getElementById('auth-message');
    messageDiv.textContent = message;
    messageDiv.className = `mt-4 p-3 rounded-md ${type === 'error' ? 'bg-red-100 text-red-700' : 'bg-green-100 text-green-700'}`;
    messageDiv.classList.remove('hidden');

    setTimeout(() => {
        messageDiv.classList.add('hidden');
    }, 5000);
}

// Upload image + drag & drop
document.getElementById('image-upload')?.addEventListener('change', function (e) {
    const preview = document.getElementById('preview');
    const file = e.target.files[0];

    if (file) {
        if (!file.type.match('image.*')) {
            showAuthMessage("Veuillez sélectionner une image valide", "error");
            return;
        }

        const reader = new FileReader();
        reader.onload = function (event) {
            preview.src = event.target.result;
            preview.classList.remove('hidden');
        };
        reader.readAsDataURL(file);
    }
});

const dropZone = document.getElementById('drop-zone');

dropZone?.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropZone.classList.add('border-indigo-500', 'bg-indigo-50');
});

dropZone?.addEventListener('dragleave', () => {
    dropZone.classList.remove('border-indigo-500', 'bg-indigo-50');
});

dropZone?.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.classList.remove('border-indigo-500', 'bg-indigo-50');

    const file = e.dataTransfer.files[0];
    if (file && file.type.match('image.*')) {
        document.getElementById('image-upload').files = e.dataTransfer.files;

        const preview = document.getElementById('preview');
        const reader = new FileReader();
        reader.onload = function (event) {
            preview.src = event.target.result;
            preview.classList.remove('hidden');
        };
        reader.readAsDataURL(file);
    } else {
        showAuthMessage("Veuillez déposer une image valide", "error");
    }
});
