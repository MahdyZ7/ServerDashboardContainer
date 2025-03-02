import { drizzle } from 'drizzle-orm/node-postgres';
import { eq, desc, sql, and, asc } from 'drizzle-orm';
import pkg from 'pg';
const { Pool } = pkg;
import { ServerMetric, ServerUser, ServerStats, TimeSeriesDataPoint } from '../client/src/types/server';
import { serverMetrics, topUsers, InsertServerMetric, InsertTopUser } from '../shared/schema';
import * as dotenv from 'dotenv';
import { dot } from 'node:test/reporters';

// Create PostgreSQL connection pool using environment variables
// const pool = new Pool({
	//   connectionString: process.env.DATABASE_URL,
	// });
	
dotenv.config();
const DB_CONFIG = {
	'host': 'postgres',
	'database': 'server_db',
	'user': 'postgres',
	'password':  process.env.POSTGRES_PASSWORD,
}

const pool = new Pool(DB_CONFIG);

// Create Drizzle instance
export const db = drizzle(pool);

// Check database connection
export async function checkConnection() {
  try {
    await pool.query('SELECT NOW()');
    console.log('PostgreSQL database connected successfully');
    return true;
  } catch (error) {
    console.error('Error connecting to PostgreSQL database:', error);
    return false;
  }
}

// Helper function to convert database datetime to string
function dateToString(date: Date): string {
  return date.toISOString();
}

// Get the latest metrics for all servers
export async function getLatestMetrics(): Promise<ServerMetric[]> {
  try {
    const latestMetricsSubquery = db
      .select({
        server_name: serverMetrics.server_name,
        max_timestamp: sql`MAX(${serverMetrics.timestamp})`.as('max_timestamp')
      })
      .from(serverMetrics)
      .groupBy(serverMetrics.server_name)
      .as('latest_metrics');

    const result = await db
      .select()
      .from(serverMetrics)
      .innerJoin(
        latestMetricsSubquery,
        and(
          eq(serverMetrics.server_name, latestMetricsSubquery.server_name),
          eq(serverMetrics.timestamp, latestMetricsSubquery.max_timestamp)
        )
      )
      .orderBy(asc(serverMetrics.server_name));
    
    return result.map(r => ({
      ...r.server_metrics,
      timestamp: dateToString(r.server_metrics.timestamp),
      cpu_load_1min: Number(r.server_metrics.cpu_load_1min),
      cpu_load_5min: Number(r.server_metrics.cpu_load_5min),
      cpu_load_15min: Number(r.server_metrics.cpu_load_15min)
    }));
  } catch (error) {
    console.error('Error fetching latest metrics:', error);
    throw error;
  }
}

// Get historical metrics for a specific server
export async function getServerMetrics(serverName: string): Promise<ServerMetric[]> {
  try {
    const metrics = await db
      .select()
      .from(serverMetrics)
      .where(eq(serverMetrics.server_name, serverName))
      .orderBy(desc(serverMetrics.timestamp))
      .limit(100);
    
    return metrics.map(metric => ({
      ...metric,
      timestamp: dateToString(metric.timestamp),
      cpu_load_1min: Number(metric.cpu_load_1min),
      cpu_load_5min: Number(metric.cpu_load_5min),
      cpu_load_15min: Number(metric.cpu_load_15min)
    }));
  } catch (error) {
    console.error(`Error fetching metrics for server ${serverName}:`, error);
    throw error;
  }
}

// Add a server metric
export async function addServerMetric(metric: InsertServerMetric): Promise<ServerMetric> {
  try {
    const [result] = await db.insert(serverMetrics).values(metric).returning();
    return {
      ...result,
      timestamp: dateToString(result.timestamp),
      cpu_load_1min: Number(result.cpu_load_1min),
      cpu_load_5min: Number(result.cpu_load_5min),
      cpu_load_15min: Number(result.cpu_load_15min)
    };
  } catch (error) {
    console.error('Error adding server metric:', error);
    throw error;
  }
}

// Add a top user
export async function addTopUser(user: InsertTopUser): Promise<ServerUser> {
  try {
    const [result] = await db.insert(topUsers).values(user).returning();
    return {
      ...result,
      timestamp: dateToString(result.timestamp),
      cpu: Number(result.cpu),
      mem: Number(result.mem),
      disk: Number(result.disk)
    };
  } catch (error) {
    console.error('Error adding top user:', error);
    throw error;
  }
}

// Get top resource users
export async function getTopUsers(): Promise<ServerUser[]> {
  try {
    const users = await db
      .select()
      .from(topUsers)
      .orderBy(desc(topUsers.cpu), desc(topUsers.mem), desc(topUsers.disk))
      .limit(20);
    
    return users.map(user => ({
      ...user,
      timestamp: dateToString(user.timestamp),
      cpu: Number(user.cpu),
      mem: Number(user.mem),
      disk: Number(user.disk)
    }));
  } catch (error) {
    console.error('Error fetching top users:', error);
    throw error;
  }
}

// Get users for a specific server
export async function getServerUsers(serverName: string): Promise<ServerUser[]> {
  try {
    const users = await db
      .select()
      .from(topUsers)
      .where(eq(topUsers.server_name, serverName))
      .orderBy(desc(topUsers.cpu), desc(topUsers.mem), desc(topUsers.disk));
    
    return users.map(user => ({
      ...user,
      timestamp: dateToString(user.timestamp),
      cpu: Number(user.cpu),
      mem: Number(user.mem),
      disk: Number(user.disk)
    }));
  } catch (error) {
    console.error(`Error fetching users for server ${serverName}:`, error);
    throw error;
  }
}

// Get system stats summary
export async function getSystemStats(): Promise<ServerStats> {
  try {
    // Get latest metrics to calculate stats
    const metrics = await getLatestMetrics();
    
    // Calculate stats
    const totalServers = metrics.length;
    const onlineServers = metrics.length; // Assuming all servers with metrics are online
    const offlineServers = 0; // We don't have this info from DB, would need to check against expected servers
    
    const totalCpuLoad = metrics.reduce((sum, server) => sum + server.cpu_load_1min, 0);
    const averageCpuLoad = totalServers > 0 ? totalCpuLoad / totalServers : 0;
    
    const totalMemoryUsage = metrics.reduce((sum, server) => sum + server.ram_percentage, 0);
    const averageMemoryUsage = totalServers > 0 ? totalMemoryUsage / totalServers : 0;
    
    return {
      totalServers,
      onlineServers,
      offlineServers,
      averageCpuLoad,
      averageMemoryUsage
    };
  } catch (error) {
    console.error('Error calculating system stats:', error);
    throw error;
  }
}
		

// Get historical CPU data for charts
export async function getCpuHistory(serverName?: string): Promise<TimeSeriesDataPoint[]> {
  try {
    const queryBase = db
      .select({
        timestamp: serverMetrics.timestamp,
        value: serverMetrics.cpu_load_1min,
        server_name: serverMetrics.server_name
      })
      .from(serverMetrics)
      .orderBy(asc(serverMetrics.timestamp))
      .limit(100);
    
    const query = serverName 
      ? queryBase.where(eq(serverMetrics.server_name, serverName))
      : queryBase;
    
    const results = await query;
    
    return results.map(row => ({
      timestamp: dateToString(row.timestamp),
      value: Number(row.value),
      server: row.server_name
    }));
  } catch (error) {
    console.error('Error fetching CPU history:', error);
    throw error;
  }
}

// Get historical memory data for charts
export async function getMemoryHistory(serverName?: string): Promise<TimeSeriesDataPoint[]> {
  try {
    const queryBase = db
      .select({
        timestamp: serverMetrics.timestamp,
        value: serverMetrics.ram_percentage,
        server_name: serverMetrics.server_name
      })
      .from(serverMetrics)
      .orderBy(asc(serverMetrics.timestamp))
      .limit(100);
    
    const query = serverName 
      ? queryBase.where(eq(serverMetrics.server_name, serverName))
      : queryBase;
    
    const results = await query;
    
    return results.map(row => ({
      timestamp: dateToString(row.timestamp),
      value: Number(row.value),
      server: row.server_name
    }));
  } catch (error) {
    console.error('Error fetching memory history:', error);
    throw error;
  }
}

// Get historical disk data for charts
export async function getDiskHistory(serverName?: string): Promise<TimeSeriesDataPoint[]> {
  try {
    const queryBase = db
      .select({
        timestamp: serverMetrics.timestamp,
        value: serverMetrics.disk_percentage,
        server_name: serverMetrics.server_name
      })
      .from(serverMetrics)
      .orderBy(asc(serverMetrics.timestamp))
      .limit(100);
    
    const query = serverName 
      ? queryBase.where(eq(serverMetrics.server_name, serverName))
      : queryBase;
    
    const results = await query;
    
    return results.map(row => ({
      timestamp: dateToString(row.timestamp),
      value: Number(row.value),
      server: row.server_name
    }));
  } catch (error) {
    console.error('Error fetching disk history:', error);
    throw error;
  }
}

// Get server names
export async function getServerNames(): Promise<string[]> {
  try {
    const results = await db
      .selectDistinct({
        server_name: serverMetrics.server_name
      })
      .from(serverMetrics)
      .orderBy(asc(serverMetrics.server_name));
    
    return results.map(row => row.server_name);
  } catch (error) {
    console.error('Error fetching server names:', error);
    throw error;
  }
}

// Initialize database connection and check tables
export async function initDb() {
  await checkConnection();
  
  // Create tables if they don't exist
  try {
    const result = await pool.query(`
      SELECT EXISTS (
        SELECT FROM information_schema.tables
        WHERE table_schema = 'public'
        AND table_name = 'server_metrics'
      );
    `);
    
    if (!result.rows[0].exists) {
      console.log('Creating database tables...');
      await pool.query(`
        CREATE TABLE IF NOT EXISTS server_metrics (
          id SERIAL PRIMARY KEY,
          timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
          server_name TEXT NOT NULL,
          architecture TEXT NOT NULL,
          operating_system TEXT NOT NULL,
          physical_cpus INTEGER NOT NULL,
          virtual_cpus INTEGER NOT NULL,
          ram_used TEXT NOT NULL,
          ram_total TEXT NOT NULL,
          ram_percentage INTEGER NOT NULL,
          disk_used TEXT NOT NULL,
          disk_total TEXT NOT NULL,
          disk_percentage INTEGER NOT NULL,
          cpu_load_1min TEXT NOT NULL,
          cpu_load_5min TEXT NOT NULL,
          cpu_load_15min TEXT NOT NULL,
          last_boot TEXT NOT NULL,
          tcp_connections INTEGER NOT NULL,
          logged_users INTEGER NOT NULL,
          active_vnc_users INTEGER NOT NULL,
          active_ssh_users INTEGER NOT NULL
        );
        
        CREATE TABLE IF NOT EXISTS top_users (
          id SERIAL PRIMARY KEY,
          timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
          server_name TEXT NOT NULL,
          "username" TEXT NOT NULL,
          cpu TEXT NOT NULL,
          mem TEXT NOT NULL,
          disk TEXT NOT NULL
        );
      `);
      console.log('Database tables created successfully');
    }
  } catch (error) {
    console.error('Error initializing database tables:', error);
    throw error;
  }
}
