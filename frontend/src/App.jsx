import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import LoginPage from './pages/Login';
import OSRSPage from './pages/osrsPage';
import { LanguageProvider, useLanguage } from './Language';

import Tabs from '@mui/material/Tabs';
import Tab from '@mui/material/Tab';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import Alert from '@mui/material/Alert';
import Button from '@mui/material/Button';

export default function App() {
    // for the welcome banner
    const [user, setUser] = useState(null);
    //For keeping track of tabs
    const [tabIndex, setTabIndex] = useState(0);

    const [sessionMessage, setSessionMessage] = useState(null)

    // For language toggle
    const { lang, toggleLanguage, t } = useLanguage();

    function allyProps(index) {
        return{
            id: `simple-tab-${index}`,
            'aria-controls': `simple-tabPanel-${index}`
        }     
    }

    //------------------------------------------/
    useEffect(() => { 
    //------------------------------------------/
        console.log("App -- useEffect -- user");
        console.log("user statue: ", user?.user);

    }, [user]);

    //------------------------------------------/
    useEffect(() => {
    //------------------------------------------/
        // Handler for expired/unauthorized requests
        const handleUnauthorized = () => {
            setUser(null); // Clear stale user state
            setTabIndex(0); // Redirect to Login tab
            setSessionMessage("Session expired or unauthorized. Please log in again.");
        };

        window.addEventListener('auth:unauthorized', handleUnauthorized);
        return () => window.removeEventListener('auth:unauthorized', handleUnauthorized);
    }, []);

    /////////////////////////////////////////////////////////////////

    return (
        <Box sx = {{flexGrow: 1, display: 'flex', height: '100vh'}}>
            {/* --- LEFT SIDEBAR CONTAINER --- */}
            <Box sx={{ 
                borderRight: 1, 
                borderColor: 'divider', 
                minWidth: '200px', 
                display: 'flex', 
                flexDirection: 'column',
                bgcolor: 'background.paper'
            }}>

                {/* Title */}
                <Box sx={{ 
                    p: 2, 
                    borderBottom: 1, 
                    borderColor: 'divider',
                    textAlign: 'center' // Optional: centers the title nicely
                }}>
                    <Typography variant="h6" sx={{ fontWeight: 'bold', color: 'primary.main' }}>
                        CRUD Project
                    </Typography>
                </Box>

                {/* Vertical Tab Navigoation */}
                <Tabs
                orientation="vertical"
                variant="scrollable"
                value={tabIndex}
                onChange={(_, i) => setTabIndex(i)} 
                aria-label="vertical tab"
                sx={{borderRight: 1, borderColor: 'divider', minWidth: '200px'}}
                >
                    {/* Login Tab */}
                    <Tab
                    label ={
                        <Typography>
                            {t('loginPage')}
                        </Typography>
                    }
                    {...allyProps(0)}
                    />
                    {/* OSRS Tab */}
                    <Tab
                    label ={
                        <Typography>
                            {t('myItems')}
                        </Typography>
                    }
                    {...allyProps(1)}
                    />
                </Tabs>
                {/* Username display*/}
                <Box sx={{ 
                    mt: 'auto', //Pin it to the bottom, otherwise it will look terrible
                    p: 2, 
                    borderTop: 1, 
                    borderColor: 'divider' 
                }}>
                    <Typography variant="subtitle1" sx={{ fontWeight: 'bold' }}>
                        {user?.user ? `Welcome, ${user.user}!` : 'Welcome, Guest!'}
                    </Typography>
                </Box>
            </Box>

            <Box sx={{ flexGrow: 1, overflow: 'auto' }}>

                {/* Experimental Alert Banner -- This might be overkill */}
                {sessionMessage && (
                    <Alert 
                        severity="warning" 
                        onClose={() => setSessionMessage(null)}
                        sx={{ mb: 2 }}
                    >
                        {sessionMessage}
                    </Alert>
                )}

                <div hidden= {tabIndex !== 0}>
                    <LoginPage
                        user={user}
                        setUser={setUser}
                    />
                </div>
                <div hidden= {tabIndex !== 1}>
                    <OSRSPage
                        user={user}
                        setUser={setUser}
                    />
                </div>
            </Box>
            
            {/* Language Toggle */}
            <Box sx={{ marginTop: 'auto', pt: 2 }}>
                <Button 
                    variant="outlined" 
                    fullWidth 
                    onClick={toggleLanguage}
                    sx={{ textTransform: 'uppercase' }}
                >
                    🌐 {lang === 'en' ? 'Español' : 'English'}
                </Button>
            </Box>
        </Box>
    );
}

ReactDOM.createRoot(document.getElementById('root')).render(
    <React.StrictMode>
        <LanguageProvider>
            <App />
        </LanguageProvider>
    </React.StrictMode>
);