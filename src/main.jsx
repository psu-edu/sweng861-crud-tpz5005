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
    //OSRS GE item price data
    const [geItemData, setgeItemData] = useState(null);

    // States for OSRS database CRUD operations
    const [newItemId, setNewItemId] = useState(''); // create - id 
    const [newItemName, setNewItemName] = useState(''); // create - name 
    const [newItemValue, setNewItemValue] = useState(''); // create - value 
    const [createStatus, setCreateStatus] = useState(null); // debug visual for create status
    const [registeredIds, setCurrentIds] = useState(''); // current ids
    const [itemToDelete, setItemToDelete] = useState(''); // delete item function

    // Initiate user login
    //------------------------------------------/
    useEffect(() => { 
    //------------------------------------------/
        fetch('https://localhost:8000/api/user', {credentials: 'include'})
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
        fetch('https://localhost:8000/api/hello', {credentials: 'include'})
            .then(response => response.json())
                .then(data => {
                    setHelloData(data);
                })
                .catch(error => {
                    console.error('Failed to fetch "hello" data:', error);
                    setErrorMsg(error.message);
                });
    }, []);

    // Gets the price of a GE item in OSRS
    // @info: This endpoint requires authentication
    //------------------------------------------/
    useEffect(() => { 
    //------------------------------------------/
        fetch('https://localhost:8000/api/runescape/price', {credentials: 'include'})
            .then(response => response.json())
                .then(data => {
                    setgeItemData(data);
                })
                .catch(error => {
                    console.error('Failed to fetch "health" data:', error);
                    setErrorMsg(error.message);
                });
    }, []);


    // Gets 'health' data form backend
    // @info: This endpoint requires authentication
    //------------------------------------------/
    useEffect(() => { 
    //------------------------------------------/
        fetch('https://localhost:8000/health', {credentials: 'include'})
            .then(response => response.json())
                .then(data => {
                    setHealthData(data);
                })
                .catch(error => {
                    console.error('Failed to fetch "health" data:', error);
                    setErrorMsg(error.message);
                });
    }, []);


    // Get IDS on launch
    //------------------------------------------/
    useEffect(() => { 
    //------------------------------------------/
        fetchCurrentIDs();
    }, []);


    /////////////////////////////////////////////


    //~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~/
    const handleCreateItem = (evnt) => {
    //~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~/   
        evnt.preventDefault()
        
        // Create the payload
        const payload = {
            item_id: parseInt(newItemId, 10),
            item_name: newItemName,
            item_value: parseInt(newItemValue, 10)
        };
        
        fetch('https://localhost:8000/api/osrs/database/create', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload),
            credentials: 'include'
        })
            .then(response => response.json())
                .then(data => {
                    setCreateStatus(data);
                    fetchCurrentIDs();
                })
                .catch(error => {
                    console.error('Failed to create item', error);
                    setErrorMsg(error.message);
                });
    };


    //~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~/
    const handleDeleteItem = (evnt) => {
    //~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~/   
        evnt.preventDefault();
        
        fetch(`https://localhost:8000/api/osrs/database/delete/${itemToDelete}`, {
            method: 'DELETE',
            credentials: 'include'
        })
            .then(response => response.json())
                .then(data => {
                    // Make sure to update the ids
                    fetchCurrentIDs();
                })
                .catch(error => {
                    console.error('Failed to create item', error);
                    setErrorMsg(error.message);
                });
    };

    // Gets all the current registered IDs int he OSRS
    // database
    //~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~/
    const fetchCurrentIDs = () => {
    //~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~/   
        fetch('https://localhost:8000/api/osrs/database/ids', {
            credentials: 'include'
        })
        .then(response => response.json())
            .then(data => {
                setCurrentIds(data);
            })
            .catch(error => {
                console.error('Failed to fetch OSRS IDs', error);
                setErrorMsg(error.message);
            });
    };


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
                        <p><strong>Hello, {userData.user.name || userData.user.username}!</strong></p>
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
                        <a href="https://localhost:8000/auth/logout" style={styles.logoutButton}>
                            Log Out
                        </a>
                    </div>
                ) : (
                    /* Rendered when the user is unauthenticated */
                    <div>
                        <p>You are not logged in.</p>
                        {/* Login Button */}
                        <a href="https://localhost:8000/auth/login" style={styles.loginButton}>
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

            {/* OSRS Endpoint */}
            <div style={styles.card}>
                <h2 style={styles.subHeading}>(3rd Party API) OSRS Grand Exchange API Response</h2>
                <pre style={styles.codeBlock}>
                    {geItemData ? JSON.stringify(geItemData, null, 2) : 'Getting OSRS pricing data...'}
                </pre>
            </div>

            {/* OSRS CReate Form */}
            <div style={styles.card}>
                <h2 style={styles.subHeading}>Create OSRS Item (OSRS Database)</h2>
                <form onSubmit={handleCreateItem} style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                    <div>
                        <label style={styles.label}>Item ID (4-number id):</label>
                        <input 
                            type="number" 
                            value={newItemId} 
                            onChange={(evnt) => setNewItemId(evnt.target.value)} 
                            placeholder="e.g. 0-30,000" 
                            style={styles.input}
                            required 
                        />
                    </div>
                    <div>
                        <label style={styles.label}>Item Name:</label>
                        <input 
                            type="text" 
                            value={newItemName} 
                            onChange={(evnt) => setNewItemName(evnt.target.value)} 
                            placeholder="e.g. Steel PlateBody" 
                            style={styles.input}
                            required 
                        />
                    </div>
                    <div>
                        <label style={styles.label}>Item Value:</label>
                        <input 
                            type="number" 
                            value={newItemValue} 
                            onChange={(evnt) => setNewItemValue(evnt.target.value)} 
                            placeholder="e.g. 10000" 
                            style={styles.input}
                            required 
                        />
                    </div>
                    {/* CREATE BUTTON */}
                    <button type="submit" style={styles.button}>Create Item</button>
                </form>
            </div>

            {/* OSRS Delete Form */}
            <div style={styles.card}>
                <h2 style={styles.subHeading}>Delete OSRS Item (OSRS Database)</h2>
                <form onSubmit={handleDeleteItem} style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                    <div>
                        <label style={styles.label}>Item to delete (4-number id):</label>
                        <input 
                            type="number" 
                            value={itemToDelete} 
                            onChange={(e) => setItemToDelete(e.target.value)}
                            placeholder="Check 'Current OSRS dataBase IDs' for current IDs" 
                            style={styles.input}
                            required 
                        />
                    </div>
                    {/* DELETE BUTTON */}
                    <button type="submit" style={styles.button}>Delete Item</button>
                </form>
            </div>

            {/* OSRS Database Create Status return */}
            <div style={styles.card}>
                <h2 style={styles.subHeading}>Current OSRS database IDs</h2>
                <pre style={styles.codeBlock}>
                    {registeredIds ? JSON.stringify(registeredIds, null, 2) : 'No IDs registered yet...'}
                </pre>
            </div>

            {/* OSRS Database Create Status return */}
            <div style={styles.card}>
                <h2 style={styles.subHeading}>OSRS Create Status</h2>
                <pre style={styles.codeBlock}>
                    {createStatus ? JSON.stringify(createStatus, null, 2) : 'No OSRS Database Create status yet...'}
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

    //OSRS elements
    label: {
        display: 'block',
        marginBottom: '4px',
        fontSize: '14px',
        fontWeight: 'bold',
        color: '#475569',
    },
    input: {
        width: '100%',
        padding: '8px',
        borderRadius: '4px',
        border: '1px solid #cbd5e1',
        boxSizing: 'border-box',
    },
    button: {
        padding: '10px 16px',
        backgroundColor: '#2563eb',
        color: '#fff',
        border: 'none',
        borderRadius: '4px',
        fontWeight: 'bold',
        cursor: 'pointer',
    },
};

ReactDOM.createRoot(document.getElementById('root')).render(
    <React.StrictMode>
        <ApiInterface />
    </React.StrictMode>
);