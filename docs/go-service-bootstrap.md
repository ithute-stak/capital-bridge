# Go ingress bootstrap integration

`RunConfiguredIngress` validates company scope, TLS configuration and the restricted PostgreSQL DSN before opening a database. It loads the certificate/key pair, configures a bounded SQL connection pool, requires a successful database ping and then runs the timestamped-HMAC event ingress with `AtomicNotificationStore` and graceful context shutdown.

**Not an executable daemon yet:** a production entry point must register a supported PostgreSQL driver, supply a driver-specific `openDB`, read the environment configuration, manage SIGTERM shutdown, provision restricted credentials and certificates, and run under a managed service unit. This bootstrap function deliberately fails closed and is covered by unit tests. Its tests do not prove a live PostgreSQL instance or TLS listener has been deployed.
