#include <fstream>
#include <string>

std::string generateRandomPassword() {
  std::string res(20, '.');
  for (int i = 0; i < 20; ++i) {
    res[i] = 'a' + rand() % 26;
  }
  return res;
}

int main() {
  int seed = time(0);
  std::ofstream outputFile("output.txt");

  for (int i = -1800; i <= 1800; i++) {
    srand(seed + i);
    outputFile << "Seed " << i << ": " << seed + i << " - "
               << "Password 1 is: " << generateRandomPassword() << '\n'
               << "Password 2 is: " << generateRandomPassword() << '\n'
               << "Password 3 is: " << generateRandomPassword() << '\n';
  }
  outputFile << std::endl;
  return 0;
}
