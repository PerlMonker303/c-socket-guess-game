#include <stdlib.h>
#include <stdio.h>
#include <sys/socket.h>
#include <arpa/inet.h>
#include <string.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <unistd.h>
#include <time.h>

#define SERVER_PORT 5005
#define SERVER_IP "127.0.0.1"
#define BACKLOG 2 // # of players

void handle_player(int* pipe, char* player, int sockfd){
	// Function to handle a player
	char letter;
	//printf("Waiting for the letter for player %s\n", player);
	read(pipe[0], &letter, sizeof(char));
	//printf("Letter for player %s: %c\n", player, letter);

	int bytes_read, result, bytes_send;
	char guess;
	// Game has started
	sleep(2);
	printf("Started game for player %s\n", player);
	
	while(1){
		// Receiving the result from the client
		bytes_read = recv(sockfd, &guess, sizeof(char), 0);
		if(bytes_read <= 0){
			break;
		}
		
		if(guess == letter){
			// Write to the parent to stop the game
			result = 1;
			printf("WINNER\n");
			write(pipe[1], &result, sizeof(int));
			bytes_send = send(sockfd, &result, sizeof(int), 0);
			break;
		}else if(guess > letter){
			// Write the client to go HIGHER
			result = 2; // HIGHER
			bytes_send = send(sockfd, &result, sizeof(int), 0);
			if(bytes_send < 0){
				break;
			}
		}else{
			// Write the client to go LOWER
			result = 3; // LOWER
			bytes_send = send(sockfd, &result, sizeof(int), 0);
			if(bytes_send < 0){
				break;
			}
		}
		
		// Read response from parent (1 - continue, 0 - stop
		//read(pipe[0], &result, sizeof(int));
		//if(result == 0){
			//break;
		//}
	}
	
	close(pipe[0]); // Closing the reading end
	close(pipe[1]); // Closing the writing end
	
	exit(0);
}

int main(){
	
	srand(time(0));
	
	// Declaring useful variables
	char* players[BACKLOG]; // Holds players' names
	int sockfd_news[BACKLOG];
	int players_count = 0;
	int pipes[BACKLOG][2]; // Pipes for communicating between processes

	// Create the server socket
	int sockfd = socket(AF_INET, SOCK_STREAM, 0);
	if(sockfd < 0){
		perror("Socket error");
		exit(1);
	}
	
	struct sockaddr_in serv_addr;
	struct sockaddr_in incom_addr;
	
	// Specify the socket information for the server
	serv_addr.sin_family = AF_INET;
	serv_addr.sin_port = htons(SERVER_PORT);
	//inet_aton(SERVER_IP, &serv_addr.sin_addr);
	serv_addr.sin_addr.s_addr = htonl(INADDR_ANY);
	memset(&serv_addr.sin_zero, '\0', 8);
	
	// Bind the socket
	if(bind(sockfd, (struct sockaddr*)&serv_addr, sizeof(struct sockaddr)) == -1){
		perror("Bind error");
		exit(1);
	}
	
	// Listen for connections
	printf("Waiting for players to join ... \n");
	listen(sockfd, BACKLOG);
	
	while(players_count < BACKLOG){
	
		// Accept connections
		int sin_len = sizeof(incom_addr); // always
		int sockfd_new = accept(sockfd, (struct sockaddr*)&incom_addr, &sin_len);
		char* ip_incoming = inet_ntoa(incom_addr.sin_addr);
		int port_incoming = ntohs(incom_addr.sin_port);
		
		// Read player's name
		int name_length;
		int bytes_read = recv(sockfd_new, &name_length, sizeof(int), 0); // first read the size
		players[players_count] = (char*)malloc(name_length * sizeof(char));
		bytes_read = recv(sockfd_new, players[players_count], name_length, 0); // then read the actual name
		sockfd_news[players_count] = sockfd_new;
		
		printf("%d/%d Player %s joined the game, address: %s:%d \n", players_count+1, BACKLOG, players[players_count], ip_incoming, port_incoming);
		
		// Create a new process to handle the current player
		pipe(pipes[players_count]); // Creating a pipe for the parent process to communicate with the child process
		if(fork() == 0){
			handle_player(pipes[players_count], players[players_count], sockfd_news[players_count]);
		}
		
		players_count++;
	}
	
	// Generate random letter
	int idx = rand() % 26 + 'a';
	char letter = (char)idx;
	printf("Generated random letter %c\n", letter);
	
	printf("Starting the game in \n3 ...\n");
	sleep(1);
	printf("2 ...\n");
	
	// Send the letter to the child processes
	for(int i=0;i<players_count;i++){
		write(pipes[i][1], &letter, sizeof(char));
	}
	
	sleep(1);
	printf("1 .. \n");
	sleep(1);
	
	printf("Game started\n");

	// Send a sign to the players (clients) that the game has started (integer 1)
	int resp = 1;
	for(int i=0;i<players_count;i++){
		int bytes_sent = send(sockfd_news[i], &resp, sizeof(int), 0);
	}
	
	int finished = 0;
	while(!finished){
		// Read from all child processes a letter until one of them guesses
		for(int i=0;i<players_count;i++){
			if(read(pipes[i][0], &resp, sizeof(char)) < 0){
				finished = 1;
			}
			if(resp == 1){
				printf("Player %s won!\n", players[i]);
				finished = 1;
			}
			
			// Writing status to child (finished = 1 - game over, 0 - continue)
			//if(write(pipes[i][1], &finished, sizeof(int)) < 0){
				//finished = 1;
			//}
			
		}
		if(resp == 1){
			break;
		}
	}
	
	printf("Game ended\n");
	sleep(1);
	
	// Closing the pipes (writing end)
	for(int i=0;i<players_count;i++){
		close(pipes[i][0]);
		close(pipes[i][1]);
	}
	
	printf("Sending other results ...\n");
	
	resp = -1; // Code for losing players
	for(int i=0;i<players_count;i++){
		send(sockfd_news[i], &resp, sizeof(int), 0); // Letting all players know they lost (besides the winner whose process has stopped already)
		close(sockfd_news[i]); // Closing all players' sockets
		wait(0); // Waiting for all child processes to end
		printf("Sent one of them :)\n");
	}
	

	
	return 0;
}
