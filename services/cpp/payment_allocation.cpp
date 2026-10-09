#include <cstdint>
#include <iostream>
#include <stdexcept>
#include <string>
// Exact integer minor-unit allocation; no floating-point monetary arithmetic.
struct Allocation { std::int64_t applied, unapplied; };
Allocation allocate(std::int64_t due, std::int64_t paid) {
    if (due < 0 || paid < 0) throw std::invalid_argument("negative money");
    const auto applied = due < paid ? due : paid;
    return {applied, paid-applied};
}
int main(int argc, char** argv) {
    if (argc != 3) return 2;
    try {
        const auto a=allocate(std::stoll(argv[1]),std::stoll(argv[2]));
        std::cout << a.applied << "," << a.unapplied << "\n";
    } catch (const std::exception&) { return 2; }
}
