// Demonstrates file I/O in C++
#include <iostream>
#include <fstream>

void fileIODemo() {
    std::ofstream out("out.txt");
    out << "Hello, file!" << std::endl;
    out.close();
    std::ifstream in("out.txt");
    std::string line;
    std::getline(in, line);
    std::cout << line << std::endl;
}
