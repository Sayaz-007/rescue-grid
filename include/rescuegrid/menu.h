#include<string>
#include<limits>

bool readLine(std::string& outStr);
bool readNonEmptyString(const std::string& prompt, std::string& outStr);
bool readInt(const std::string& prompt,int& outVal,int minVal = std::numeric_limits<int>::min(),int maxVal = std::numeric_limits<int>::max());
//void handleRegisterIncident(RescueManager& manager);