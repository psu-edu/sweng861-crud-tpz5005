import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import OSRSPage from './osrsPage';
import LoginPage from './Login';
import { apiClient } from '../apiClient';
import '@testing-library/jest-dom';

// =================================================================/
// Set up external dependencies
// =================================================================/
// Set up the apiClient
//----------------------------------------------/
jest.mock('../apiClient', () => ({
//----------------------------------------------/
  apiClient: jest.fn(),
}));

// Use the keys in the language struct
//----------------------------------------------/
jest.mock('../Language', () => ({
//----------------------------------------------/
  useLanguage: () => ({
    t: (key) => key,
  }),
}));

// =================================================================/
// Set up UI test
// =================================================================/
//----------------------------------------------/
describe('OSRSPage Component Unit Tests', () => {
//----------------------------------------------/
    // Create a mock user object
    const mockUser = { id: 1, name: 'TestUser' };

    // Here we are clearing all the histories and return values. This
    // will stop previous tests from altering the UI state
    beforeEach(() => {
        jest.clearAllMocks();
        apiClient.mockResolvedValue({});
    });

    // =============================================================/
    // 1) Render UI with null user
    // =============================================================/
    //~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~/
    test('fetch initial state without a user', async () => {
    //~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~/
        // Attempt to render the page without a user
        render(<OSRSPage user={null} />);

        // Confirm no network calls were made
        expect(apiClient).not.toHaveBeenCalled();

        // Verify that a placeholder element is present on the UI
        expect(await screen.findByText('Getting OSRS pricing data...')).toBeInTheDocument();
    });

    // =============================================================/
    // 2) Get Price and IDs when user is valid
    // =============================================================/
    //~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~/
    test('get price data and ids when the user if valid', async () => {
    //~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~/
        // Create mock data that client will return
        const mockPriceData = { price: 100, item: 'Abyssal Whip' };
        const mockIds = [4151, 11840];

        // mockResolvedValueOnce chains return values for sequential apiClient calls:
        // Get the price and IDs
        apiClient
        .mockResolvedValueOnce(mockPriceData)
        .mockResolvedValueOnce(mockIds);

        // Render UI with valid user
        render(<OSRSPage user={mockUser} />);

        // waitFor is used for async UI updates
        await waitFor(() => {
            // Confirm endpoints were called in exact order
            expect(apiClient).toHaveBeenNthCalledWith(1, '/api/runescape/price');
            expect(apiClient).toHaveBeenNthCalledWith(2, '/api/osrs/database/ids');
        });

        // Verify that mock data is present on the UI
        expect(await screen.findByText(/Abyssal Whip/i)).toBeInTheDocument();
        expect(await screen.findByText(/11840/)).toBeInTheDocument();
    });

    // ===============================================================/
    // 3) Create Item
    // ===============================================================/
    //~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~/
    test('Creates items and inspects the results code block', async () => {
    //~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~/
        const mockCreateResponse = { success: true, id: 4151 };

        //Simulate the sequential api calls 
        apiClient
        .mockResolvedValueOnce({ price: 100 }) //Mount: /api/runescape/price
        .mockResolvedValueOnce([100]) //Mount: /api/osrs/database/ids
        .mockResolvedValueOnce(mockCreateResponse) //Post: /api/osrs/database/create
        .mockResolvedValueOnce([100, 4151]); // Fetch id list

        // Render the UI page
        render(<OSRSPage user={mockUser} />);

        // wait for mount api calls to finish
        await waitFor(() => {
            expect(apiClient).toHaveBeenCalledWith('/api/runescape/price');
        });

        // Get the UI elements by what they should display
        const idInput = screen.getByPlaceholderText('e.g. 0-30,000');
        const nameInput = screen.getByPlaceholderText('itemNamePlaceholder');
        const valueInput = screen.getByPlaceholderText('e.g. 10000');
        const submitBtn = screen.getByRole('button', { name: /create/i });

        // Enter in simulated data
        await userEvent.type(idInput, '4151');
        await userEvent.type(nameInput, 'Abyssal Whip');
        await userEvent.type(valueInput, '1500000');

        // Simulate a submit click
        await userEvent.click(submitBtn);

        // Verify that the apiClient gateway can called with a POST for create
        await waitFor(() => {
            expect(apiClient).toHaveBeenCalledWith('/api/osrs/database/create', 
                expect.objectContaining({
                    method: 'POST',
                    body: JSON.stringify({
                    item_id: 4151,
                    item_name: 'Abyssal Whip',
                    item_value: 1500000,
                    }),
                }),
            )
        });

        // Verify that the ID is included in the UI
        const matches = await screen.findAllByText(/4151/);
        expect(matches.length).toBeGreaterThan(0);

        // Verify create form is blank after item creation
        expect(idInput.value).toBe('');
        expect(nameInput.value).toBe('');
        expect(valueInput.value).toBe('');
    });

    // ===============================================================/
    // 4) Simulate a item read
    // ===============================================================/
    //~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~/
    test('simulates read and checks status code block', async () => {
    //~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~/
        const mockReadResponse = { item_id: 4151, 
                                   item_name: 'Abyssal Whip', 
                                   item_value: 1500000 };
        
        // Simulate the sequential api calls
        apiClient
        .mockResolvedValueOnce({ price: 100 }) //Mount: /api/runescape/price
        .mockResolvedValueOnce([4151]) //Mount: /api/osrs/database/ids
        .mockResolvedValueOnce(mockReadResponse) // GET request result
        .mockResolvedValueOnce([4151]); // Refetched IDs

        render(<OSRSPage user={mockUser} />);
        
        // Wait for mount to settle
        await waitFor(() => {
            expect(apiClient).toHaveBeenCalledWith('/api/runescape/price');
        });   

        // I may have discovered poor UI coding practice. Both Read and delete share identical 
        // placeholder strings. the first element corresponds to Read, so i have hardcoded '[0]'
        const readInputs = screen.getAllByPlaceholderText('checkCurrentIdsPlaceholder');
        const readInput = readInputs[0]; // first element is read
        const readBtn = screen.getByRole('button', { name: 'getItemInfoBut' });

        // Simulate a ID entry into the read form
        await userEvent.type(readInput, '4151');
        await userEvent.click(readBtn);

        // Verify that the apiClient has a GET request to the /read/${item_id} endpoint
        await waitFor(() => {
            expect(apiClient).toHaveBeenCalledWith('/api/osrs/database/read/4151', {
                method: 'GET',
            });
        });

        // Verify that the UI has the expected item information from a Read request
        expect(await screen.findByText(/Abyssal Whip/i)).toBeInTheDocument();
        //expect(await screen.findByText(JSON.stringify(mockReadResponse, null, 2))).toBeInTheDocument();
    });

    // ===============================================================/
    // 5) Simulate Item Deletion
    // ===============================================================/
    //~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~/
    test('Simulates Item Deletion and resets input', async () => {
    //~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~/
        // A delete response only contains a bool
        const mockDeleteResponse = { deleted: true };

        // Simulate sequential api calls
        apiClient
        .mockResolvedValueOnce({ price: 100 })
        .mockResolvedValueOnce([4151])
        .mockResolvedValueOnce(mockDeleteResponse) // DELETE request
        .mockResolvedValueOnce([]); //IDs should be empty

        // Render the UI
        render(<OSRSPage user={mockUser} />);

        // Wait for mount to settle
        await waitFor(() => {
            expect(apiClient).toHaveBeenCalledWith('/api/runescape/price');
        });

        // Again the read and delete have the same placehold, the second index corresponds to 
        // delete
        const deleteInputs = screen.getAllByPlaceholderText('checkCurrentIdsPlaceholder');
        const deleteInput = deleteInputs[1]; // Delete
        const deleteBtn = screen.getByRole('button', { name: 'deleteItem' });
        
        // Simulate a user attempting to delete
        await userEvent.type(deleteInput, '4151');
        await userEvent.click(deleteBtn);

        // Verify the apiClient has a delete request to /delete/${item_id}
        await waitFor(() => {
            expect(apiClient).toHaveBeenCalledWith('/api/osrs/database/delete/4151', {
                method: 'DELETE',
            });
        });

        // Verify that the IDs field is null
        expect(await screen.findByText(/deleted/i)).toBeInTheDocument();
        expect(deleteInput).toHaveValue(null);
    });

    // ===============================================================/
    // 6) Simulate a delte all
    // ===============================================================/
    //~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~/
    test('Simulates delete all', async () => {
    //~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~/
        // Since i have a warning window, we need to to simulate the user
        // clicking confirm to continue with delete all
        jest.spyOn(window, 'confirm').mockImplementation(() => true);

        // Simulate sequential api calls
        apiClient
        .mockResolvedValueOnce({ price: 100 })
        .mockResolvedValueOnce([4151])
        .mockResolvedValueOnce({ deletedAll: true })
        .mockResolvedValueOnce([]);

        //Render the UI 
        render(<OSRSPage user={mockUser} />);

        // Wait for mount to settle
        await waitFor(() => {
            expect(apiClient).toHaveBeenCalledWith('/api/runescape/price');
        });

        //Simulate the user clicking delete all
        const deleteAllBtn = screen.getByRole('button', { name: 'deleteAllItems' });
        await userEvent.click(deleteAllBtn);

        // Verify that the warning window has been rendered
        expect(window.confirm).toHaveBeenCalledWith('confirmDeleteAll');

        // verify that the apiClient has a delete request for /delete-all endpoint
        await waitFor(() => {
            expect(apiClient).toHaveBeenCalledWith('/api/osrs/database/delete-all', {
                method: 'DELETE',
            });
        });
    });

    // ===============================================================/
    // 7) Simulate ownership
    // ===============================================================/
    //~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~/
    test('UI Displays 403 when we do not own the item', async () => {
    //~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~/
        const errorMessage = 'You are not authorized to view this item.';

        // Initial OSRSPage requests
        apiClient
            .mockResolvedValueOnce({ price: 100 })  //Mount: /api/runescape/price
            .mockResolvedValueOnce([1333])          //Mount: /api/osrs/database/ids
            .mockRejectedValueOnce(new Error(errorMessage)); // /read/1333

        //Render the UI 
        render(<OSRSPage user={mockUser} />);

        // Wait for mount to settle
        await waitFor(() => {
            expect(apiClient).toHaveBeenNthCalledWith(1, '/api/runescape/price');
            expect(apiClient).toHaveBeenNthCalledWith(2, '/api/osrs/database/ids');
        });

        // const input = screen.getByPlaceholderText(/Check 'Current OSRS database IDs' for current IDs/i);
        // const searchBtn = screen.getByRole('button', { name: /Search Item/i });

        const readInputs = screen.getAllByPlaceholderText('checkCurrentIdsPlaceholder');
        const input = readInputs[0];

        const searchBtn = screen.getByRole('button', {name: 'getItemInfoBut'});

        // Enter item ID
        await userEvent.type(input, '1333');

        // Search for item
        await userEvent.click(searchBtn);

        // Verify that the endpoint was called
        await waitFor(() => {
            expect(apiClient).toHaveBeenNthCalledWith(3, '/api/osrs/database/read/1333',{method: 'GET',});
        });

        // Verify error is displayed
        expect(await screen.findByText(errorMessage)).toBeInTheDocument();
    });


    // ===============================================================/
    // 8) Simulate Login wiht Github
    // ===============================================================/
    test('GitHub login button links to login endpoint', async () => {
        apiClient.mockResolvedValueOnce({
            authenticated: false
        });

        render(
            <LoginPage
                user={null}
                setUser={jest.fn()}
                onLoginSuccess={jest.fn()}
            />
        );

        const githubButton = await screen.findByRole('link', {name: /loginWithGithub/i});

        expect(githubButton).toHaveAttribute(
            'href',
            'https://localhost:8000/auth/login'
        );
    });


    // ===============================================================/
    // 8) Simulate GitHub callback
    // ===============================================================/
    test('displays GitHub user after successful OAuth authentication', async () => {
        const mockOAuthUser = {
            authenticated: true,
            user: {
                username: 'githubUser',
                name: 'GitHub User',
                avatar_url: 'https://github.com/githubuser.png'
            }
        };

        apiClient.mockResolvedValueOnce(mockOAuthUser);

        const setUser = jest.fn();

        render(
            <LoginPage
                user={null}
                setUser={setUser}
                onLoginSuccess={jest.fn()}
            />
        );

        expect(
            await screen.findByText(/Hello, GitHub User!/i)
        ).toBeInTheDocument();

        expect(
            screen.getByAltText('User Avatar')
        ).toBeInTheDocument();

        expect(setUser).toHaveBeenCalled();
    });


    // ===============================================================/
    // Test the Error state UI banner
    // ===============================================================/
    //~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~/
    test('displays API errors gracefully in the UI banner', async () => {
    //~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~/
        // Adding this to get rid of a terminal output
        const consoleSpy = jest.spyOn(console, 'error').mockImplementation(() => {});

        const errorMessage = 'Network error fetching data';

        // Force a UI error
        apiClient.mockRejectedValueOnce(new Error(errorMessage));

        //Render the UI
        render(<OSRSPage user={mockUser} />);

        // Verify that the error banner has the expected error message
        expect(await screen.findByText(errorMessage)).toBeInTheDocument();
        
        consoleSpy.mockRestore();
    });
});