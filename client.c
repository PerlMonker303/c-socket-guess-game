#include <stdlib.h>
#include <stdio.h>
#include <sys/socket.h>
#include <arpa/inet.h>
#include <string.h>
#include <sys/types.h>
#include <unistd.h>
#include <netdb.h>

#define MY_PORT 0
#define DEST_PORT 5005
#define DEST_IP "10.42.0.1"
#define INPUT_SIZE 10

int main(int argc, char* argv[]){

	if(argc < 2){
		printf("usage: player_name\n");
		exit(1);
	}
	
	printf("Welcome player %s\n", argv[1]);
	int name_length = strlen(argv[1]);
	// Create the socket
	int sockfd = socket(AF_INET, SOCK_STREAM, 0);
	if(sockfd < 0){
		perror("Socket error");
		exit(1);
	}
	
	struct sockaddr_in my_addr;
	struct sockaddr_in dest_addr;
	
	// Specify the client's address
	my_addr.sin_family = AF_INET;
	my_addr.sin_port = htons(MY_PORT);
	my_addr.sin_addr.s_addr = htonl(INADDR_ANY);
	memset(&my_addr.sin_zero, '\0', 8);
	
	// Bind the address to the socket
	if(bind(sockfd, (struct sockaddr*)&my_addr, sizeof(struct sockaddr)) == -1){
		perror("Bind error");
		exit(1);
	}
	
	// Declare the server's address
	dest_addr.sin_family = AF_INET;
	dest_addr.sin_port = htons(DEST_PORT);
	dest_addr.sin_addr.s_addr = inet_addr(DEST_IP);
	/*
	struct hostent *h;
	h = gethostbyname(argv[2]);
	printf("%d\n", h->h_length);
	printf("%s\n", h->h_addr_list[0]);
	memcpy((char *) &dest_addr.sin_addr.s_addr, h->h_addr_list[0], h->h_length);
	printf("%s\n", DEST_IP);
	*/
	memset(&dest_addr.sin_zero, '\0', 8);
	
	// Connect to the server	
	printf("Connecting to server ...\n");
	if(connect(sockfd, (struct sockaddr*)&dest_addr, sizeof(struct sockaddr)) == -1){
		perror("Connection error");
		exit(1);
	}
	
	// Send the player's name to the server
	int bytes_sent = send(sockfd, &name_length, sizeof(int), 0); // first send the length of the name
	bytes_sent = send(sockfd, argv[1], strlen(argv[1]), 0); // then send the actual name
	
	printf("Connected. Waiting for the game to begin ...\n");
	int resp = 0;
	int bytes_read = recv(sockfd, &resp, sizeof(int), 0);
	
	if(resp == 0 || bytes_read == 0){
		printf("Game failed to start.\n");
		exit(1);
	}
	
	printf("---Start---\n");
	char* input = (char*)malloc(INPUT_SIZE * sizeof(char));
	while(1){
		printf(">");
		// Read a letter from console
		scanf("%s", input);
		//read(0, input, 1);
		if(strlen(input) == 0 || strlen(input) > 1){
			printf("Please input a single character\n");
			continue;
		}
		//printf("Read %c\n", input[0]);
		// Send the character
		//printf("Sending character %c to server ... \n", input[0]);
		bytes_sent = send(sockfd, input, sizeof(char), 0);
		if(bytes_sent < 0){
			break;
		}
		//printf("Sent\n");
		
		// Receive a result
		bytes_read = recv(sockfd, &resp, sizeof(int), 0);
		if(bytes_read < 0){
			break;
		}
		if(resp == 1){ // WON
			printf("YOU WON! \n");
			break;		
		}
		if(resp == 0){ // LOST
			printf("YOU LOST! \n");
			break;
		}
		if(resp == 2){ // HIGHER
			printf("Higher\n");
		}else if(resp == 3){ // LOWER
			printf("Lower\n");
		}
	}
	printf("---Game ended---\n");
	free(input);
	
}
