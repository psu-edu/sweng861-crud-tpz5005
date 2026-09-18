// src/LanguageContext.jsx
import React, { createContext, useState, useContext } from 'react';

export const translations = {
    en: {
        // Auth & Navigation
        password: "Password",
        usernameOrEmail: "Username / Email",
        loginWithGithub: "Log in with GitHub",
        crudProject: "CRUD Project",
        loginPage: "Login Page",
        authentication: "Authentication",
        authenticationStatusOAuth: "Authentication Status (3-Legged OAuth2)",
        loginError: "Login Error:",
        signIn: "Sign In",
        logIn: "Log In",
        logOut: "Log Out",
        hello: "Hello",


        // Database & Headers
        myItems: "My Items",
        osrsDatabaseTitle: "My OldSchool RuneScape (OSRS) Database",
        osrsGeApiResponse: "OSRS Grand Exchange API Response",
        currentOsrsDbIds: "Current OSRS database IDs",
        fetchError: "Fetch Error:",
        deleteOsrsItemHeader: "Delete OSRS Item (Delete)",

        // Actions & Buttons
        readMany: "Read Many",
        create: "Create",
        createItem: "Create Item",
        read: "Read",
        getItemInfo: "Get Item Info (Read)",
        getItemInfoBut: "Get Item Info",
        delete: "Delete",
        deleteItem: "Delete Item",
        deleteAllItems: "Delete All Items",
        viewDetails: "View Details",
        hideDetails: "Hide Details",
        itemNamePlaceholder: "e.g., Steel Platebody, Hammer, Sword, Potion",

        // Form Labels & Inputs
        itemId: "Item ID (number):",
        itemName: "Item Name:",
        itemValue: "Item Value:",
        numberLabel: "number",
        itemToRead: "Item to Read (number)",
        itemToDelete: "Item to delete (number)",
        adminDeleteWarning: "Requires Admin privileges. This will wipe the ENTIRE items table.",
        checkCurrentIdsPlaceholder: "Check 'Current OSRS database IDs' for current IDs",

        // Status Headers
        createOsrsItem: "Create OSRS Item (Create)",
        osrsCreateStatus: "OSRS Create Status",
        osrsReadStatus: "OSRS Read Status",
        deleteOsrsItem: "Delete OSRS Item",
        osrsDeleteStatus: "OSRS Delete Status",
        confirmDeleteAll: "Are you REALLY SURE you want to delete all the OSRS items?",
    },
    es: {
        // Auth & Navigation
        password: "Contraseña",
        usernameOrEmail: "Usuario / Correo electrónico",
        loginWithGithub: "Iniciar sesión con GitHub",
        crudProject: "Proyecto CRUD",
        loginPage: "Página de inicio de sesión",
        authentication: "Autenticación",
        authenticationStatusOAuth: "Estado de autenticación (OAuth2 de 3 pasos)",
        loginError: "Error de inicio de sesión:",
        signIn: "Iniciar sesión",
        logIn: "Iniciar sesión",
        logOut: "Cerrar sesión",
        hello: "Hola",

        // Database & Headers
        myItems: "Mis objetos",
        osrsDatabaseTitle: "Mi base de datos de OldSchool RuneScape (OSRS)",
        osrsGeApiResponse: "Respuesta de la API Grand Exchange de OSRS",
        currentOsrsDbIds: "IDs actuales en la base de datos OSRS",
        fetchError: "Error de consulta:",
        deleteOsrsItemHeader: "Eliminar objeto OSRS (Eliminar)",

        // Actions & Buttons
        readMany: "Leer varios",
        create: "Crear",
        createItem: "Crear objeto",
        read: "Leer",
        getItemInfo: "Obtener información del objeto (Leer)",
        getItemInfoBut: "Obtener información del objeto",
        delete: "Eliminar",
        deleteItem: "Eliminar objeto",
        deleteAllItems: "Eliminar todos los objetos",
        viewDetails: "Ver detalles",
        hideDetails: "Ocultar detalles",
        itemNamePlaceholder: "p. ej., Peto de acero, Martillo, Espada, Poción",

        // Form Labels & Inputs
        itemId: "ID del objeto (número):",
        itemName: "Nombre del objeto:",
        itemValue: "Valor del objeto:",
        numberLabel: "número",
        itemToRead: "Objeto para leer (número)",
        itemToDelete: "Objeto para eliminar (número)",
        adminDeleteWarning: "Requiere privilegios de administrador. Esto borrará TODA la tabla de objetos.",
        checkCurrentIdsPlaceholder: "Consulta 'IDs actuales en la base de datos OSRS' para ver los IDs actuales",

        // Status Headers
        createOsrsItem: "Crear objeto OSRS (Crear)",
        osrsCreateStatus: "Estado de creación OSRS",
        osrsReadStatus: "Estado de lectura OSRS",
        deleteOsrsItem: "Eliminar objeto OSRS",
        osrsDeleteStatus: "Estado de eliminación OSRS",
        confirmDeleteAll: "¿Está REALMENTE SEGURO de que desea eliminar todos los objetos de OSRS?",
    }
}

const LanguageContext = createContext();

export function LanguageProvider({ children }) {
    const [lang, setLang] = useState('en');

    const toggleLanguage = () => {
        setLang((prev) => (prev === 'en' ? 'es' : 'en'));
    };

    // Helper function to get text by key
    const t = (key) => translations[lang][key] || key;

    return (
        <LanguageContext.Provider value={{ lang, toggleLanguage, t }}>
            {children}
        </LanguageContext.Provider>
    );
}

export const useLanguage = () => useContext(LanguageContext);