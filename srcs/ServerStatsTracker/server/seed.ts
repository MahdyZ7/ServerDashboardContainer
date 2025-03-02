import { addServerMetric, addTopUser, db } from './db';
import { InsertServerMetric, InsertTopUser } from '../shared/schema';
import { sql } from 'drizzle-orm';

// const SERVER_NAMES = ['KSRC1', 'KSRC2', 'KSRC3', 'KSRC4', 'KSRC5'];
// const OS_TYPES = ['Ubuntu 22.04 LTS', 'CentOS 8.5', 'Debian 11', 'RHEL 9.0', 'Fedora 36'];
// const ARCHITECTURES = ['x86_64', 'amd64'];
// const LAST_BOOT_DATES = [
//   '2023-12-05 08:32:15',
//   '2024-01-12 10:15:30',
//   '2024-01-30 06:45:12',
//   '2024-02-10 12:20:45',
//   '2024-02-15 09:10:22'
// ];
// const USER_NAMES = [
//   'root', 'jenkins', 'admin', 'sysadmin', 'mongodb', 
//   'postgres', 'nginx', 'apache', 'tomcat', 'mysql',
//   'oracle', 'backup', 'developer', 'webadmin', 'ansible'
// ];

// // Generate a random number within a range
// function randomInRange(min: number, max: number): number {
//   return Math.floor(Math.random() * (max - min + 1)) + min;
// }

// // Generate a random decimal within a range with specified precision
// function randomDecimal(min: number, max: number, precision: number = 2): number {
//   const value = Math.random() * (max - min) + min;
//   return parseFloat(value.toFixed(precision));
// }

// // Format a size in GB
// function formatSize(sizeGB: number): string {
//   return `${sizeGB.toFixed(2)} GB`;
// }

// // Generate a server metric for a specific server
// function generateServerMetric(serverName: string, timestamp: Date): InsertServerMetric {
//   const serverIndex = SERVER_NAMES.indexOf(serverName);
  
//   // Base values that stay somewhat consistent per server
//   const physicalCpus = randomInRange(2, 8);
//   const virtualCpus = physicalCpus * 2;
//   const ramTotalGB = randomInRange(16, 256);
//   const diskTotalGB = randomInRange(500, 4000);
  
//   // Dynamic values that change with each measurement
//   const cpuLoad1 = randomDecimal(0.1, virtualCpus * 0.7);
//   const cpuLoad5 = randomDecimal(
//     Math.max(0.1, cpuLoad1 - randomDecimal(0.1, 0.5)), 
//     cpuLoad1 + randomDecimal(0.1, 0.8)
//   );
//   const cpuLoad15 = randomDecimal(
//     Math.max(0.1, cpuLoad5 - randomDecimal(0.2, 0.7)), 
//     cpuLoad5 + randomDecimal(0.1, 0.3)
//   );
  
//   const ramUsedGB = randomDecimal(ramTotalGB * 0.2, ramTotalGB * 0.8);
//   const ramPercentage = Math.round((ramUsedGB / ramTotalGB) * 100);
  
//   const diskUsedGB = randomDecimal(diskTotalGB * 0.3, diskTotalGB * 0.9);
//   const diskPercentage = Math.round((diskUsedGB / diskTotalGB) * 100);
  
//   return {
//     timestamp,
//     server_name: serverName,
//     architecture: ARCHITECTURES[randomInRange(0, ARCHITECTURES.length - 1)],
//     operating_system: OS_TYPES[serverIndex % OS_TYPES.length],
//     physical_cpus: physicalCpus,
//     virtual_cpus: virtualCpus,
//     ram_used: formatSize(ramUsedGB),
//     ram_total: formatSize(ramTotalGB),
//     ram_percentage: ramPercentage,
//     disk_used: formatSize(diskUsedGB),
//     disk_total: formatSize(diskTotalGB),
//     disk_percentage: diskPercentage,
//     cpu_load_1min: cpuLoad1.toString(),
//     cpu_load_5min: cpuLoad5.toString(),
//     cpu_load_15min: cpuLoad15.toString(),
//     last_boot: LAST_BOOT_DATES[serverIndex % LAST_BOOT_DATES.length],
//     tcp_connections: randomInRange(50, 500),
//     logged_users: randomInRange(1, 15),
//     active_vnc_users: randomInRange(0, 3),
//     active_ssh_users: randomInRange(1, 8)
//   };
// }

// // Generate top users for a specific server
// function generateTopUsers(serverName: string, timestamp: Date, count: number = 5): InsertTopUser[] {
//   const users: InsertTopUser[] = [];
  
//   // Create a shuffled copy of USER_NAMES
//   const shuffledUsers = [...USER_NAMES].sort(() => 0.5 - Math.random());
  
//   for (let i = 0; i < Math.min(count, shuffledUsers.length); i++) {
//     // Higher resource usage for first users (they're the "top" users after all)
//     const cpuUsage = randomDecimal(
//       Math.max(0.1, 10 - i), // Higher min for top users
//       Math.max(1, 90 - (i * 10)) // Higher max for top users
//     );
    
//     const memUsage = randomDecimal(
//       Math.max(0.1, 5 - (i * 0.5)),
//       Math.max(1, 60 - (i * 8))
//     );
    
//     const diskUsage = randomDecimal(0.1, 30 - (i * 3));
    
//     users.push({
//       timestamp,
//       server_name: serverName,
//       user: shuffledUsers[i],
//       cpu: cpuUsage.toString(),
//       mem: memUsage.toString(),
//       disk: diskUsage.toString()
//     });
//   }
  
//   return users;
// }

// // Create metrics for the past 7 days, with measurements every 30 minutes
// async function generateHistoricalData(): Promise<void> {
//   // Create a timestamp for 7 days ago
//   const startDate = new Date();
//   startDate.setDate(startDate.getDate() - 7);
  
//   // Set to midnight
//   startDate.setHours(0, 0, 0, 0);
  
//   const now = new Date();
//   let currentTimestamp = new Date(startDate);
  
//   while (currentTimestamp < now) {
//     for (const serverName of SERVER_NAMES) {
//       // Add a server metric
//       const metric = generateServerMetric(serverName, currentTimestamp);
//       try {
//         await addServerMetric(metric);
//         console.log(`Added metric for ${serverName} at ${currentTimestamp.toISOString()}`);
//       } catch (error) {
//         console.error(`Error adding metric for ${serverName}:`, error);
//       }
      
//       // Only add top users every 6 hours to save on data
//       if (currentTimestamp.getHours() % 6 === 0 && currentTimestamp.getMinutes() === 0) {
//         const users = generateTopUsers(serverName, currentTimestamp);
//         for (const user of users) {
//           try {
//             await addTopUser(user);
//             console.log(`Added top user ${user.user} for ${serverName}`);
//           } catch (error) {
//             console.error(`Error adding top user for ${serverName}:`, error);
//           }
//         }
//       }
//     }
    
//     // Advance by 30 minutes
//     currentTimestamp.setMinutes(currentTimestamp.getMinutes() + 30);
//   }
  
//   console.log('Historical data generation complete');
// }

// // Function to seed the database
// export async function seedDatabase(): Promise<void> {
//   console.log('Starting to seed database with test data...');
  
//   try {
//     // First check if we already have data
//     const result = await db.execute(sql`SELECT COUNT(*) FROM server_metrics`);
    
//     // Safely parse the count, handling the unknown type
//     let count = 0;
//     if (result.rows && result.rows.length > 0 && result.rows[0].count !== undefined) {
//       const countValue = result.rows[0].count;
//       count = typeof countValue === 'string' ? parseInt(countValue, 10) : 
//               typeof countValue === 'number' ? countValue : 0;
//     }
    
//     if (count > 0) {
//       console.log('Database already has data, skipping seed');
//       return;
//     }
    
//     await generateHistoricalData();
//     console.log('Database seeded successfully');
//   } catch (error) {
//     console.error('Error seeding database:', error);
//     // Check if it's a table doesn't exist error
//     if (error instanceof Error && error.message.includes("relation") && error.message.includes("does not exist")) {
//       console.log('Tables do not exist yet, will try again after they are created');
//     } else {
//       throw error;
//     }
//   }
// }