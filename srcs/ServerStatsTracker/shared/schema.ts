import { pgTable, text, serial, integer, boolean, timestamp, decimal } from "drizzle-orm/pg-core";
import { createInsertSchema } from "drizzle-zod";
import { z } from "zod";

// Server metrics schema
export const serverMetrics = pgTable("server_metrics", {
  id: serial("id").primaryKey(),
  timestamp: timestamp("timestamp").notNull().defaultNow(),
  server_name: text("server_name").notNull(),
  architecture: text("architecture").notNull(),
  operating_system: text("operating_system").notNull(),
  physical_cpus: integer("physical_cpus").notNull(),
  virtual_cpus: integer("virtual_cpus").notNull(),
  ram_used: text("ram_used").notNull(),
  ram_total: text("ram_total").notNull(),
  ram_percentage: integer("ram_percentage").notNull(),
  disk_used: text("disk_used").notNull(),
  disk_total: text("disk_total").notNull(),
  disk_percentage: integer("disk_percentage").notNull(),
  cpu_load_1min: text("cpu_load_1min").notNull(),
  cpu_load_5min: text("cpu_load_5min").notNull(),
  cpu_load_15min: text("cpu_load_15min").notNull(),
  last_boot: text("last_boot").notNull(),
  tcp_connections: integer("tcp_connections").notNull(),
  logged_users: integer("logged_users").notNull(),
  active_vnc_users: integer("active_vnc_users").notNull(),
  active_ssh_users: integer("active_ssh_users").notNull()
});

// Top users schema
export const topUsers = pgTable("top_users", {
  id: serial("id").primaryKey(),
  timestamp: timestamp("timestamp").notNull().defaultNow(),
  server_name: text("server_name").notNull(),
  user: text("username").notNull(),
  cpu: text("cpu").notNull(),
  mem: text("mem").notNull(),
  disk: text("disk").notNull()
});

// User schema for authentication (if needed)
export const users = pgTable("users", {
  id: serial("id").primaryKey(),
  username: text("username").notNull().unique(),
  password: text("password").notNull(),
});

// Insert schemas
export const insertServerMetricSchema = createInsertSchema(serverMetrics).omit({ id: true });
export const insertTopUserSchema = createInsertSchema(topUsers).omit({ id: true });
export const insertUserSchema = createInsertSchema(users).omit({ id: true });

// Types
export type InsertServerMetric = z.infer<typeof insertServerMetricSchema>;
export type InsertTopUser = z.infer<typeof insertTopUserSchema>;
export type InsertUser = z.infer<typeof insertUserSchema>;

export type ServerMetric = typeof serverMetrics.$inferSelect;
export type TopUser = typeof topUsers.$inferSelect;
export type User = typeof users.$inferSelect;
