Project Document: TCP Game
Course: Computer Networks
Project Title: TCP Game
Project Type: Pair Programming (2 clients communicating)
Total Duration of Game: 5 minutes per match

1. Project Overview
In this project, you will implement a simplified TCP-like protocol simulation between two clients that communicate with each other over a socket connection. This is basically a game between two students. Both clients will exchange packets with the following parameters:
* seq - Sequence number
* ack - Acknowledgment number
* rwnd - Receiver window size
* length - Data length
The communication follows strict rules to mimic TCP behavior, including flow control and error detection. The game is turn-based, meaning packets are sent alternately - one client cannot send multiple consecutive packets unless required by the rules.
The goal is to design a communication mechanism where each client:
* Sends valid and logical packets.
* Detects invalid packets from the other side.
* Manages flow control using rwnd.
* Try to earn points by correctly identifying the other client's mistakes or exploiting undetected mistakes.

2. Game Rules
Rule 1 - Packet Validity & Error Detection
* Each incoming packet must be checked for logical consistency. Based on previously received packets, the receiving client must decide if the new packet's parameters are possible or impossible (e.g., incorrect sequence number, inconsistent ack, invalid rwnd behavior, invalid length, etc.).
* If a client receives a logically impossible packet, it must:
1. Send back an "ERROR" notification (without seq, ack, rwnd, or length).
2. Gain +1 point for detecting the error.
* If a client sends an incorrect packet, and the receiver fails to detect it and continues the communication, then the sender gains +1 point.

Rule 2 - Quick response
o If there is no response for 45 seconds, the side who must send a response will lose 1 point.
o ATTENTION: Assume that client has sent a message, and if the server side is expected to send a message, the server side will lose 1 point. 
o BUT, If a rwnd is sent with a value of zero and no packets are sent by either side within 45 seconds, the player who advertised the zero rwnd will lose points. However, if the other player erroneously sends a packet during this interval, that sending player will lose points instead.

Rule 3 - Game Duration
* The game starts with a score of 0 - 0.
* After 5 minutes, the game ends, and the score determines the winner.

Rule 4 - Game Duration
* In each 15 seconds, increase rwnd by 20. It represents the process of buffered data.

Additional Constraints
* Go-Back-N ARQ protocol must always be used.
* There is no timeout mechanism. Only fast retransmit (3 double ACK) should trigger retransmissions for lost packets. Check the lecture presentations for more information.
* A receiver may pretend to have received incorrectly any packet, at its discretion.
* Besides the text-based interface, you must also generate a visual graph (like the ones in the lecture slides) showing the packet flow timeline between the two clients.
* Assume that seq and ack numbers are 0 and rwnd is 50 at the beginning of the game.
* No need for constant packet length. Packet lengths may vary.

3. Implementation Requirements
* Language: Any programming language is allowed, but Python or Java is recommended for simplicity.
* Architecture: Two independent client programs communicating over sockets (can run on localhost).
* Core functions to implement:
o Packet creation and parsing (seq, ack, rwnd, length).
o Logic to check validity of incoming packets.
o Error reporting and scoring mechanism.
o Go-Back-N with double ACK retransmissions.
o Handling of rwnd = 0 and timing out after 45 seconds.
o Packet timeline graph generation.
* User interface: It should look like the TCP segment exchange diagrams shown in the lecture slides, with arrows representing packets over time.

4. Report & Submission
Each group must submit a project report including:
1. Introduction & Architecture - Describe the design and how your program works.
2. Implementation Details - Explain key functions, data structures, and mechanisms.
3. Source Code 

5. Demo Guidelines
During the Week 14 demo, you will run your program live for the instructor.
* Small mistakes may be fixed immediately.
* You should be able to explain your code and answer conceptual questions about TCP mechanisms.
* If you want to improve your demo score, you can revise and re-demo in Week 15.

6. FAQ (Frequently Asked Questions)
Q1: Do we need a real server?
No. The game is client-to-client. You can use localhost with two sockets. One client can act as a listener to accept connections.

Q2: How strict should the packet validity checks be?
You must design checks that catch obvious logical errors (e.g., sequence numbers jumping randomly, acknowledgment numbers that don't make sense, inconsistent rwnd). Minor variations are okay if justified.

Q3: What if both clients send invalid packets simultaneously?
The game is turn-based, so this should not happen. If it does because of an implementation error, the receiving side should handle it gracefully and send an error.

Q5: What should the timeline graph look like?
Use any visualization library (e.g., Matplotlib in Python). It should look similar to the TCP segment exchange diagrams shown in class slides, with arrows representing packets over time.

7. Tips
* Start by implementing basic communication before adding game logic.
* Use clear logging for debugging packet validity.
* Test unusual scenarios (e.g., fake ACKs, window = 0, invalid seq).
* Modularize your code so that the game logic and TCP-like mechanisms are separated.

