import React from 'react';
import {useEffect, useState, StrictMode} from 'react';
import ReactDOM from 'react-dom/client';

/**
 * @function ApiInterface
 * @description Interfaces with the API to retrieve backend calls
 */
/***********************************************/
function ApiInterface() {
/***********************************************/
    // Holds response for hello backend calls
    const [helloData, setHelloData] = useState(null);
    // Holds response for health backend calls
    const [healthData, setHealthData] = useState(null);
    //Debug error message
    const [errorMsg, setErrorMsg] = useState(null);
    //User login data
    const [userData, setUserData] = useState(null);

    // Initiate user login
    //------------------------------------------/
    useEffect(() => { 
    //------------------------------------------/
        fetch('http://127.0.0.1:8000/api/user', {credentials: 'include'})
            .then(response => response.json())
                .then(data => {
                    setUserData(data);
                })
                .catch(error => {
                    console.error('Failed to get authentication data:', error);
                    setErrorMsg(error.message);
                });
    }, []);

    // Gets 'hello' data form backend
    //------------------------------------------/
    useEffect(() => { 
    //------------------------------------------/
        fetch('http://127.0.0.1:8000/api/hello')
            .then(response => response.json())
                .then(data => {
                    setHelloData(data);
                })
                .catch(error => {
                    console.error('Failed to fetch "hello" data:', error);
                    setErrorMsg(error.message);
                });
    }, []);

    // Gets 'health' data form backend
    // @info: This endpoint requires authentication
    //------------------------------------------/
    useEffect(() => { 
    //------------------------------------------/
        fetch('http://127.0.0.1:8000/health', {credentials: 'include'})
            .then(response => response.json())
                .then(data => {
                    setHealthData(data);
                })
                .catch(error => {
                    console.error('Failed to fetch "health" data:', error);
                    setErrorMsg(error.message);
                });
    }, []);

    /////////////////////////////////////////////

    return (
        <div style = {{  padding: '20px', fontFamily: 'Arial, sans-serif' }}>
            <h1 style = {styles.heading}> Week 1 Assignment 3</h1>

            {/* Debug banner */}
            {errorMsg && (
                <div style={{ color: 'red', marginBottom: '20px' }}>
                    <strong> Fetch Error: </strong> {errorMsg}
                </div>
            )}
           
            {/* Login interface */}
            <div style={styles.card}>
                <h2 style={styles.subHeading}>Authentication Status (3-Legged OAuth2)</h2>
                {userData?.authenticated ? (
                    /* Rendered when the user has successfully logged in via OAuth */
                    <div>
                        <p><strong>Welcome back, {userData.user.name || userData.user.username}!</strong></p>
                        {userData.user.avatar_url && (
                            <img 
                                src={userData.user.avatar_url} 
                                alt="User Avatar" 
                                width="60" 
                                style={{ borderRadius: '50%', marginBottom: '10px' }} 
                            />
                        )}
                        <br />
                        {/* Logout Button */}
                        <a href="http://127.0.0.1:8000/auth/logout" style={styles.logoutButton}>
                            Log Out
                        </a>
                    </div>
                ) : (
                    /* Rendered when the user is unauthenticated */
                    <div>
                        <p>You are not logged in.</p>
                        {/* Login Button */}
                        <a href="http://127.0.0.1:8000/auth/login" style={styles.loginButton}>
                            Log in with GitHub
                        </a>
                    </div>
                )}
            </div>
         
            {/* Hello endpoint */}
            <div style = { styles.card}>
                <h2 style = {styles.subHeading}>Hello API Response</h2>
                <pre style = {styles.codeBlock}>
                    {helloData ? JSON.stringify(helloData, null, 2) : 'Getting hello data...'}
                </pre>
            </div>
            
            {/* Health Endpoint */}
            <div style = {styles.card}>
                <h2 style = {styles.subHeading}>Health API Response</h2>
                <pre style={styles.codeBlock}>
                    {healthData ? JSON.stringify(healthData, null, 2) : 'Getting health data...'}
                </pre>
            </div>

        </div>
    );
}

// Inline CSS Styles Object
const styles = {
    container: {
        maxWidth: '700px',
        margin: '40px auto',
        padding: '24px',
        fontFamily: 'Arial, sans-serif',
        backgroundColor: '#f8f9fa',
        borderRadius: '8px',
        boxShadow: '0 4px 6px rgba(0,0,0,0.1)',
    },
    heading: {
        color: '#2c3e50',
        borderBottom: '2px solid #e2e8f0',
        paddingBottom: '12px',
        marginTop: 0,
    },
    subHeading: {
        fontSize: '18px',
        color: '#34495e',
        marginTop: 0,
    },
    card: {
        backgroundColor: '#ffffff',
        padding: '16px',
        borderRadius: '6px',
        border: '1px solid #e2e8f0',
        marginTop: '16px',
    },
    codeBlock: {
        backgroundColor: '#1e293b',
        color: '#38bdf8',
        padding: '12px',
        borderRadius: '4px',
        overflowX: 'auto',
        fontSize: '14px',
        margin: 0,
    },
    loginButton: {
        display: 'inline-block',
        padding: '10px 16px',
        backgroundColor: '#24292e',
        color: '#fff',
        textDecoration: 'none',
        borderRadius: '4px',
        fontWeight: 'bold',
    },
    logoutButton: {
        display: 'inline-block',
        marginTop: '10px',
        padding: '6px 12px',
        backgroundColor: '#e53e3e',
        color: '#fff',
        textDecoration: 'none',
        borderRadius: '4px',
    },
};

ReactDOM.createRoot(document.getElementById('root')).render(
    <React.StrictMode>
        <ApiInterface />
    </React.StrictMode>
);