# College-Project---MQTT-Based-Traffic-Simulation

yes, this started as a university project.  
no, it did not stay “just a basic python assignment”.

built for the course *Introduction to Python in Engineering*, this project simulates a rectangular city where autonomous cars transport passengers under a centralized control system.

---

### the city

- grid-based layout (horizontal and vertical streets only)
- two lanes per street (one per direction)
- no overtaking
- discrete-time simulation

all vehicles are autonomous and fully controlled by a central unit that:
- assigns cars to passengers
- computes routes
- dynamically adjusts speeds to prevent collisions
- stores full vehicle state history

---

### how communication works

everything talks through a communication layer that supports:

- direct function calls (local mode)
- MQTT (distributed mode)

the MQTT implementation uses **paho-mqtt**, meaning cars and passengers can run on different machines if needed

because yes, if we're simulating distributed systems, we might as well do it properly

---

### concurrency (aka the fun part)

vehicles and the control center update state concurrently
to avoid turning the simulation into undefined behavior theater, locks are used to protect shared state

cars periodically publish their:
- position
- velocity

and the control center adjusts speeds to maintain a safe distance (at least one lane width apart)

---

### why this project is actually interesting

this wasn’t just about moving dots on a grid.

it touches on:
- distributed communication
- message-based architecture
- synchronization
- simulation modeling
- centralized vs distributed control tradeoffs

basically: a polite introduction to systems thinking, disguised as a python class project.

---

this project can be configured with:
- number of cars
- number of passengers
- street count and dimensions
- initial positions

because hardcoded simulations are boring.
