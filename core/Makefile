CXX ?= g++
CXXFLAGS ?= -O3 -march=native -fPIC -std=c++17 -fopenmp -Wall -Wextra -Iinclude
TARGET ?= libinvariantq.so

SRCS = src/statevector.cpp src/density_matrix.cpp src/stabilizer.cpp src/mps.cpp src/api.cpp
OBJS = $(SRCS:.cpp=.o)

all: $(TARGET)

$(TARGET): $(OBJS)
	$(CXX) -shared -fopenmp -o $@ $^

src/%.o: src/%.cpp
	$(CXX) $(CXXFLAGS) -c $< -o $@

clean:
	rm -f src/*.o $(TARGET)

.PHONY: all clean
