import type { Express } from "express";
import { createServer, type Server } from "http";
import { storage } from "./storage";
import * as db from "./db";
import { ServerMetric, ServerSummary } from "../client/src/types/server";

export async function registerRoutes(app: Express): Promise<Server> {

  // Get the latest metrics for all servers
  app.get('/api/metrics/latest', async (req, res) => {
    try {
      const metrics = await db.getLatestMetrics();
      res.json(metrics);
    } catch (error) {
      console.error('Error fetching latest metrics:', error);
      res.status(500).json({ message: 'Error fetching metrics' });
    }
  });

  // Get metrics for a specific server
  app.get('/api/metrics/server/:serverId', async (req, res) => {
    try {
      const serverId = req.params.serverId;
      const metrics = await db.getServerMetrics(serverId);
      res.json(metrics);
    } catch (error) {
      console.error(`Error fetching metrics for server ${req.params.serverId}:`, error);
      res.status(500).json({ message: 'Error fetching server metrics' });
    }
  });

  // Get top resource users
  app.get('/api/users/top', async (req, res) => {
    try {
      const users = await db.getTopUsers();
      res.json(users);
    } catch (error) {
      console.error('Error fetching top users:', error);
      res.status(500).json({ message: 'Error fetching top users' });
    }
  });

  // Get users for a specific server
  app.get('/api/users/server/:serverId', async (req, res) => {
    try {
      const serverId = req.params.serverId;
      const users = await db.getServerUsers(serverId);
      res.json(users);
    } catch (error) {
      console.error(`Error fetching users for server ${req.params.serverId}:`, error);
      res.status(500).json({ message: 'Error fetching server users' });
    }
  });

  // Get system stats summary
  app.get('/api/stats', async (req, res) => {
    try {
      const stats = await db.getSystemStats();
      res.json(stats);
    } catch (error) {
      console.error('Error fetching system stats:', error);
      res.status(500).json({ message: 'Error fetching system stats' });
    }
  });

  // Get server names and status summary
  app.get('/api/servers', async (req, res) => {
    try {
      // Get latest metrics to determine status
      const metrics = await db.getLatestMetrics();
      const servers: ServerSummary[] = metrics.map(metric => {
        let status: 'online' | 'warning' | 'offline' = 'online';
        
        // Determine status based on thresholds
        if (metric.ram_percentage > 85 || metric.disk_percentage > 85 || 
            metric.cpu_load_1min / metric.virtual_cpus > 0.8) {
          status = 'warning';
        }
        
        return {
          server_name: metric.server_name,
          status,
          ip_address: `192.168.1.${Math.floor(Math.random() * 254) + 1}`, // Placeholder IP
          last_updated: metric.timestamp
        };
      });
      
      res.json(servers);
    } catch (error) {
      console.error('Error fetching servers:', error);
      res.status(500).json({ message: 'Error fetching servers' });
    }
  });

  // Get historical CPU data for charts
  app.get('/api/metrics/history/cpu', async (req, res) => {
    try {
      const data = await db.getCpuHistory();
      res.json(data);
    } catch (error) {
      console.error('Error fetching CPU history:', error);
      res.status(500).json({ message: 'Error fetching CPU history' });
    }
  });

  // Get historical CPU data for a specific server
  app.get('/api/metrics/history/cpu/:serverId', async (req, res) => {
    try {
      const serverId = req.params.serverId;
      const data = await db.getCpuHistory(serverId);
      res.json(data);
    } catch (error) {
      console.error(`Error fetching CPU history for server ${req.params.serverId}:`, error);
      res.status(500).json({ message: 'Error fetching CPU history' });
    }
  });

  // Get historical memory data for charts
  app.get('/api/metrics/history/memory', async (req, res) => {
    try {
      const data = await db.getMemoryHistory();
      res.json(data);
    } catch (error) {
      console.error('Error fetching memory history:', error);
      res.status(500).json({ message: 'Error fetching memory history' });
    }
  });

  // Get historical memory data for a specific server
  app.get('/api/metrics/history/memory/:serverId', async (req, res) => {
    try {
      const serverId = req.params.serverId;
      const data = await db.getMemoryHistory(serverId);
      res.json(data);
    } catch (error) {
      console.error(`Error fetching memory history for server ${req.params.serverId}:`, error);
      res.status(500).json({ message: 'Error fetching memory history' });
    }
  });

  // Get historical disk data for a specific server
  app.get('/api/metrics/history/disk/:serverId', async (req, res) => {
    try {
      const serverId = req.params.serverId;
      const data = await db.getDiskHistory(serverId);
      res.json(data);
    } catch (error) {
      console.error(`Error fetching disk history for server ${req.params.serverId}:`, error);
      res.status(500).json({ message: 'Error fetching disk history' });
    }
  });

  // Get comparison data for CPU
  app.get('/api/metrics/comparison/cpu', async (req, res) => {
    try {
      const data = await db.getCpuHistory();
      res.json(data);
    } catch (error) {
      console.error('Error fetching CPU comparison data:', error);
      res.status(500).json({ message: 'Error fetching CPU comparison data' });
    }
  });

  // Get comparison data for memory
  app.get('/api/metrics/comparison/memory', async (req, res) => {
    try {
      const data = await db.getMemoryHistory();
      res.json(data);
    } catch (error) {
      console.error('Error fetching memory comparison data:', error);
      res.status(500).json({ message: 'Error fetching memory comparison data' });
    }
  });

  // Get comparison data for disk
  app.get('/api/metrics/comparison/disk', async (req, res) => {
    try {
      const data = await db.getDiskHistory();
      res.json(data);
    } catch (error) {
      console.error('Error fetching disk comparison data:', error);
      res.status(500).json({ message: 'Error fetching disk comparison data' });
    }
  });

  const httpServer = createServer(app);
  return httpServer;
}
