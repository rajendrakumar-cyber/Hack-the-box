#include <iostream>
#include <cstring>
#include <string>
#include <unistd.h>
#include "openssl/sha.h"

using namespace std;

void sha256(const string & inputStr, unsigned char * sha256_output)
{
    SHA256((const unsigned char*)inputStr.c_str(), inputStr.size(), sha256_output);
}

string generateRandomPassword()
{
    string res(20, '.');
    for (int i = 0; i < 20; ++i) {
        res[i] = 'a' + rand() % 26;
    }
    return res;
}

int main() {
    srand(time(0));
    while (1)
    {
        string serverPassword = generateRandomPassword();
        cout << "Password is " << serverPassword.substr(0,5) << "..............." << endl;
        cout << "Your guess: ";
        string userPassword;
        cin >> userPassword;

        // Calculate sha256 hashes to protect from a timing attack.
        char serverPasswordHash[SHA256_DIGEST_LENGTH];
        char userPasswordHash[SHA256_DIGEST_LENGTH];
        sha256(serverPassword, (unsigned char*)serverPasswordHash);
        sha256(userPassword, (unsigned char*)userPasswordHash);

        // DO NOT USE strcmp() as the buffers are not NULL-terminated!!!
        if (strncmp(serverPasswordHash, userPasswordHash, SHA256_DIGEST_LENGTH) == 0) {
            system("cat /flag");
            break;
        }
        cout << "Wrong! Try again in a second..." << endl;
        sleep(1);
    }

    return 0;
}
