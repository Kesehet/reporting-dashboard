import { createServer } from 'miragejs';
import transactionsData from './data/transactionsData.json';

export function MockServerHandler() {
    // Implement the mock server logic
    return createServer({
        environment: 'test',
        urlPrefix: 'http://localhost:5000',            
        routes() {
            this.post('/login', (schema, request) => {
                const attrs = JSON.parse(request.requestBody);
                if (attrs.email === 'testuser' && attrs.password === 'testpassword') {
                    return { message: 'Login successful.', token: 'dummyToken' };
                } else {
                    return { message: 'Login failed.' };
                }
            });

            // Will match transaction service endpoint, like http://localhost:5000/?startDate=....
            this.get('/', () => {
                return transactionsData;
            });            
        }
    });
}
