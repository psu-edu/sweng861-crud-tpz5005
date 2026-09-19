import React from 'react';
import {useEffect, useState, StrictMode} from 'react';
//import { useAuth } from '../context/AuthContext';
import { styles } from '../styles';
import { apiClient } from '../apiClient';
import { useLanguage } from '../Language';

/***********************************************/
export default function OSRSPage(user, setUser) {
/***********************************************/

    //OSRS GE item price data
    const [geItemData, setgeItemData] = useState(null);

    // States for OSRS database CRUD operations
    const [newItemId, setNewItemId] = useState(''); // create - id 
    const [newItemName, setNewItemName] = useState(''); // create - name 

    const [registeredIds, setCurrentIds] = useState(''); // current ids

    const [newItemValue, setNewItemValue] = useState(''); // create - value 
    const [showCreateStatus, setShowCreateStatus] = useState(false);
    const [createStatus, setCreateStatus] = useState(null); // debug visual for create status

    

    const [itemToRead, setItemToRead] = useState(''); // delete item function
    const [showReadStatus, setShowReadStatus] = useState(false);
    const [readStatus, setReadStatus] = useState(null); // Delete function Status

    const [itemToDelete, setItemToDelete] = useState(''); // delete item function
    const [showDeleteStatus, setShowDeleteStatus] = useState(false);
    const [deleteStatus, setDeleteStatus] = useState(null); // Delete function Status

    const [deleteAllStatus, setDeleteAllStatus] = useState(null); // Delete all button
    
    // For language switching
    const { t } = useLanguage();

    //Debug error message
    const [errorMsg, setErrorMsg] = useState(null);


    // This is triggered whenever the 'user' state changes
    // It was made specifically for the custom login
    //------------------------------------------/
    useEffect(() => {
    //------------------------------------------/
    // Only run if a user is logged in
    if (!user) return;

    const fetchOSRSData = async () => {
        try {
            const price = await apiClient('/api/runescape/price');
            const ids = await apiClient('/api/osrs/database/ids');
            
            // Set your component state here
            setgeItemData(price);
            setCurrentIds(ids);   
        } catch (err) {
            console.error('Failed to fetch OSRS data:', err);
        }
    };

    fetchOSRSData();
    }, [user]);


    // Gets the price of a GE item in OSRS
    // @info: This endpoint requires authentication
    //------------------------------------------/
    useEffect(() => { 
    //------------------------------------------/
        apiClient('/api/runescape/price')
            .then(data => {
                setgeItemData(data);
                fetchCurrentIDs();
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
    const handleCreateItem = async (evnt) => {
    //~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~/   
        evnt.preventDefault()
        
        // Create the payload
        const payload = {
            item_id: parseInt(newItemId, 10),
            item_name: newItemName,
            item_value: parseInt(newItemValue, 10)
        };

        try {
            const data = await apiClient('/api/osrs/database/create', {
                method: 'POST',
                body: JSON.stringify(payload)
            });
            setCreateStatus(data);
            fetchCurrentIDs();
        } catch (error) {
            console.error('Failed to create item:', error);
            setErrorMsg(error.message);
        }
    };


    //~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~/
    const handleReadItem = async (evnt) => {
    //~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~/   
        evnt.preventDefault();
        try {
            const data = await apiClient(`/api/osrs/database/read/${itemToRead}`, {
                method: 'GET'
            });

            //Set the delete response status
            setReadStatus(data);
            // Make sure to update the ids
            fetchCurrentIDs();
        } catch (error) {
            setReadStatus(error.message);
            console.error('Failed to read item:', error);
            setErrorMsg(error.message);
        }
    };

    //~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~/
    const handleDeleteItem = async (evnt) => {
    //~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~/   
        evnt.preventDefault();
        try {
            const data = await apiClient(`/api/osrs/database/delete/${itemToDelete}`, {
                method: 'DELETE'
            });

            //Set the delete response status
            setDeleteStatus(data);
            // Make sure to update the ids
            fetchCurrentIDs();
        } catch (error) {
            setDeleteStatus(error.message);
            console.error('Failed to delete item:', error);
            setErrorMsg(error.message);
        }
    };


    //~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~/
    const handleDeleteAll = async (evnt) => {
    //~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~/   
        evnt.preventDefault();
        
        // Safety check prompt
        if (!window.confirm(t('confirmDeleteAll'))) {
            return;
        }
        
        try {
            const data = await apiClient('/api/osrs/database/delete-all', {
                method: 'DELETE'
            });
            
            setDeleteAllStatus(data);
            // Make sure to update the ids
            fetchCurrentIDs();
        } catch (error) {
            console.error('Failed to delete all items', error);
            setErrorMsg(error.message);
        }
    };


    // Gets all the current registered IDs int he OSRS
    // database
    //~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~/
    const fetchCurrentIDs = () => {
    //~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~/     
        apiClient('/api/osrs/database/ids')
            .then(data => {
                setCurrentIds(data);
            })
            .catch(error => {
                if (error.message.includes('No IDs were found')) {
                setCurrentIds(null); 
                } else {
                    console.error('Failed to fetch OSRS IDs', error);
                    setErrorMsg(error.message);
                }
            });
    };

    /////////////////////////////////////////////

    return (
        <div style = {{  padding: '20px', fontFamily: 'Arial, sans-serif' }}>
            <h1 style = {styles.heading}> {t('osrsDatabaseTitle')} </h1>

            {/* Debug banner */}
            {errorMsg && (
                <div style={{ color: 'red', marginBottom: '20px' }}>
                    <strong> {t('fetchError')} </strong> {errorMsg}
                </div>
            )}

            {/* OSRS Endpoint */}
            <div style={styles.card}>
                <h2 style={styles.subHeading}> {t('osrsGeApiResponse')} </h2>
                <pre style={styles.codeBlock}>
                    {geItemData ? JSON.stringify(geItemData, null, 2) : 'Getting OSRS pricing data...'}
                </pre>
            </div>

            {/* OSRS Database Create Status return */}
            <div style={styles.card}>
                <h2 style={styles.subHeading}> {t('currentOsrsDbIds')} </h2>
                <pre style={styles.codeBlock}>
                    {registeredIds ? JSON.stringify(registeredIds, null, 2) : 'No IDs registered yet...'}
                </pre>
            </div>

            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '20px' }}>
                {/* OSRS Create Form */}
                <div style={{ ...styles.card, flex: '1 1 300px', marginTop: 0}}>
                    <h2 style={styles.subHeading}> {t('createOsrsItem')} </h2>
                    <form onSubmit={handleCreateItem} style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                        <div>
                            <label style={styles.label}> {t('itemId')} </label>
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
                            <label style={styles.label}> {t('itemName')} </label>
                            <input 
                                type="text" 
                                value={newItemName} 
                                onChange={(evnt) => setNewItemName(evnt.target.value)} 
                                placeholder={t('itemNamePlaceholder')} 
                                style={styles.input}
                                required 
                            />
                        </div>
                        <div>
                            <label style={styles.label}> {t('itemValue')} </label>
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
                        <button type="submit" style={styles.button}> {t('createItem')} </button>
                    </form>
                </div>

                {/* OSRS Database Create Status return */}
                <div style={{ ...styles.card, flex: '1 1 300px', marginTop: 0 }}>
                    <h2 style={styles.subHeading}> {t('osrsCreateStatus')} </h2>

                    {!showCreateStatus ? (
                        <button 
                            type="button"
                            onClick={() => setShowCreateStatus(true)} 
                            style={styles.button}
                        >
                            {t('viewDetails')}
                        </button>
                    ) : (
                        <div style={{ display: 'flex', flexWrap: 'wrap', flexDirection: 'column', gap: '10px' }}>
                            <pre style={styles.codeBlock}>
                                {createStatus ? JSON.stringify(createStatus, null, 2) : 'No Create information yet...'}
                            </pre>
                            <button 
                                type="button"
                                onClick={() => setShowCreateStatus(false)} 
                                style={{ ...styles.button, backgroundColor: '#6c757d' }}
                            >
                                {t('hideDetails')}
                            </button>
                        </div>
                    )}
                </div>

            </div>

            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '20px' }}>
                {/* OSRS Read Form */}
                <div style={{ ...styles.card, flex: '1 1 300px', marginTop: 0}}>
                    <h2 style={styles.subHeading}> {t('getItemInfo')} </h2>
                    <form onSubmit={handleReadItem} style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                        <div>
                            <label style={styles.label}> {t('itemToRead')} </label>
                            <input 
                                type="number" 
                                value={itemToRead} 
                                onChange={(e) => setItemToRead(e.target.value)}
                                placeholder={t('checkCurrentIdsPlaceholder')} 
                                style={styles.input}
                                required 
                            />
                        </div>
                        {/* READ BUTTON */}
                        <button type="submit" style={styles.button}> {t('getItemInfoBut')} </button>
                    </form>
                </div>

                <div style={{ ...styles.card, flex: '1 1 300px', marginTop: 0 }}>
                    <h2 style={styles.subHeading}> {t('osrsReadStatus')} </h2>

                    {!showReadStatus ? (
                        <button 
                            type="button"
                            onClick={() => setShowReadStatus(true)} 
                            style={styles.button}
                        >
                            {t('viewDetails')}
                        </button>
                    ) : (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                            <pre style={styles.codeBlock}>
                                {readStatus ? JSON.stringify(readStatus, null, 2) : 'No Item information yet...'}
                            </pre>
                            <button 
                                type="button"
                                onClick={() => setShowReadStatus(false)} 
                                style={{ ...styles.button, backgroundColor: '#6c757d' }}
                            >
                                {t('hideDetails')}
                            </button>
                        </div>
                    )}
                </div>
            </div>
            
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '20px' }}>
                {/* OSRS Delete Form */}
                <div style={{ ...styles.card, flex: '1 1 300px', marginTop: 0}}>
                    <h2 style={styles.subHeading}> {t('deleteOsrsItemHeader')} </h2>
                    <form onSubmit={handleDeleteItem} style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                        <div>
                            <label style={styles.label}> {t('itemToDelete')} </label>
                            <input 
                                type="number" 
                                value={itemToDelete} 
                                onChange={(e) => setItemToDelete(e.target.value)}
                                placeholder={t('checkCurrentIdsPlaceholder')} 
                                style={styles.input}
                                required 
                            />
                        </div>
                        {/* DELETE BUTTON */}
                        <button type="submit" style={styles.button}> {t('deleteItem')} </button>
                    </form>
                </div>

                <div style={{ ...styles.card, flex: '1 1 300px', marginTop: 0 }}>
                    <h2 style={styles.subHeading}> {t('osrsDeleteStatus')} </h2>

                    {!showDeleteStatus ? (
                        <button 
                            type="button"
                            onClick={() => setShowDeleteStatus(true)} 
                            style={styles.button}
                        >
                            {t('viewDetails')}
                        </button>
                    ) : (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                            <pre style={styles.codeBlock}>
                                {deleteStatus ? JSON.stringify(deleteStatus, null, 2) : 'No Delete information yet...'}
                            </pre>
                            <button 
                                type="button"
                                onClick={() => setShowDeleteStatus(false)} 
                                style={{ ...styles.button, backgroundColor: '#6c757d' }}
                            >
                                {t('hideDetails')}
                            </button>
                        </div>
                    )}
                </div>
            </div>

            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '20px' }}>
                {/* OSRS Delete ALL Form */}
                <div style={{ ...styles.card, flex: '1 1 300px', marginTop: 0}}>
                    <h2 style={styles.subHeading}> {t('deleteAllItems')} </h2>
                    <p style={{ fontSize: '14px', color: '#64748b', marginBottom: '12px', marginTop: '0' }}>
                        {t('adminDeleteWarning')}
                    </p>
                    <button onClick={handleDeleteAll} style={styles.dangerButton}>
                        {t('deleteAllItems')}
                    </button>

                    {/* Show the status of the delete-all request if it exists */}
                    {deleteAllStatus && (
                        <pre style={{...styles.codeBlock, marginTop: '12px'}}>
                            {JSON.stringify(deleteAllStatus, null, 2)}
                        </pre>
                    )}
                </div>
            </div>
            
        </div>
    );
}