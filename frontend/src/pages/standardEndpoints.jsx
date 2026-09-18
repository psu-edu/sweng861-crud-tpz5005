import React from 'react';
import {useEffect, useState, StrictMode} from 'react';
import { styles } from '../styles';

/***********************************************/
export default function StandardEndpoints() {
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
        fetch('https://localhost:8000/api/hello', {credentials: 'include'})
        //fetch('${base_url}/api/hello', {credentials: 'include'})
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
        fetch('https://localhost:8000/health', {credentials: 'include'})
        //fetch('${base_url}/health', {credentials: 'include'})
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
            <h1 style = {styles.heading}> Week 3 Assignment</h1>

            {/* Debug banner */}
            {errorMsg && (
                <div style={{ color: 'red', marginBottom: '20px' }}>
                    <strong> Fetch Error: </strong> {errorMsg}
                </div>
            )}

            <div style={{ display: 'flex', gap: '20px' }}>
                {/* Hello endpoint */}
                <div style = {{ ...styles.card, flex: 1, marginTop: 0}}>
                    <h2 style = {styles.subHeading}>Hello API Response</h2>
                    <pre style = {styles.codeBlock}>
                        {helloData ? JSON.stringify(helloData, null, 2) : 'Getting hello data...'}
                    </pre>
                </div>
                
                {/* Health Endpoint */}
                <div style = {{ ...styles.card, flex: 1, marginTop: 0}}>
                    <h2 style = {styles.subHeading}>Health API Response</h2>
                    <pre style={styles.codeBlock}>
                        {healthData ? JSON.stringify(healthData, null, 2) : 'Getting health data...'}
                    </pre>
                </div>
            </div>

        </div>
    );
}