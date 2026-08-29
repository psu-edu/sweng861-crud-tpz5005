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
    //------------------------------------------/
    useEffect(() => { 
    //------------------------------------------/
        fetch('http://127.0.0.1:8000/health')
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

            {errorMsg && (
                <div style={{ color: 'red', marginBottom: '20px' }}>
                    <strong> Fetch Error: </strong> {errorMsg}
                </div>
            )}

            <div style = { styles.card}>
                <h2 style = {styles.subHeading}>Hello API Response</h2>
                <pre style = {styles.codeBlock}>
                    {helloData ? JSON.stringify(helloData, null, 2) : 'Getting hello data...'}
                </pre>
            </div>

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
};

ReactDOM.createRoot(document.getElementById('root')).render(
    <React.StrictMode>
        <ApiInterface />
    </React.StrictMode>
);