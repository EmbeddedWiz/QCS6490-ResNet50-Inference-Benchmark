CXX := g++
CXXFLAGS := -O2 -std=c++20 -pthread

TARGET := cpu-stressor-affinity
SOURCE := main_affinity.cpp

.PHONY: all clean

all: $(TARGET)

$(TARGET): $(SOURCE)
	$(CXX) $(CXXFLAGS) $(SOURCE) -o $(TARGET)

clean:
	rm -f $(TARGET)
