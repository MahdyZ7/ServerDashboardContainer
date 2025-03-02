
import pkg from 'pg';
const { Pool } = pkg;
import dotenv from 'dotenv';

// Load environment variables
dotenv.config();

console.log('Remote connection helper for Server Monitoring Dashboard');
console.log('----------------------------------------------------');
console.log('Use this script to test database connectivity from external sources');

// Create PostgreSQL connection pool
const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  ssl: process.env.NODE_ENV === 'production' ? { rejectUnauthorized: false } : false,
});

// Check database connection
async function checkConnection() {
  try {
    const result = await pool.query('SELECT NOW()');
    console.log('PostgreSQL database connected successfully at:', result.rows[0].now);
    console.log('\nTo connect from your local machine:');
    console.log('1. Set DATABASE_URL environment variable to:', process.env.DATABASE_URL);
    console.log('2. If using SSL, you may need to set SSL_REJECT_UNAUTHORIZED=0 for testing');
    return true;
  } catch (error) {
    console.error('Error connecting to PostgreSQL database:', error);
    return false;
  } finally {
    // Close the pool
    await pool.end();
  }
}

// Run the check
checkConnection();
