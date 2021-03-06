
"""Basic Neighborhood - exchanging the hosting periods and rooms assigned to two lectures of different courses """

class CellBasicNeighborhood(object):
    """
    Cell to keep data about course for BasicNeighborhood structure
    Index - index on list in timeTable[period]

    """

    def __init__(self, courseId, period, index):
        self.courseId = courseId
        self.period = period
        self.index = index


class BasicNeighborhood(object):
    """
    Structure containing all possible swaps between courses

    """
    def __init__(self, data):
        self.basicList = []
        self.data = data

    def clearBasicList(self):
        self.basicList = []

    def addCell(self, cellFirst, cellSecond):

        """
        Add possible swap between courses

        :param cellFirst: first cell
        :param cellSecond:  second cell
        """
        self.basicList.append((cellFirst, cellSecond))

    def getBasicList(self):
        """
        Get list containing possible swaps

        :return:basic list
        """
        return self.basicList



    def checkSimpleSwapMove(self, timetable, neighbourhoodList,  courseIdSecond, slot):
        """
        Check is swap between two courses if possible regarding other courses in slot (neighbourhoodList
        if courseIdSecond can be assigned to slot

        :param timetable: timetable
        :param neighbourhoodList: neighbourhoodList containing all conflicts between courses
        :param courseIdSecond: id of second course
        :param slot:
        :return:
        """
        for x in timetable[slot]:
            if (x[0] in neighbourhoodList[courseIdSecond]) or (x[0] == courseIdSecond):
                return False
        return True


    def checkIfNotInBasicNeighbourhood(self, courseIdFirst, slotFirst, courseIdSecond, slotSecond):
        """
        Check if swap between courses exists in BasicNeighbourhood structure

        :param courseIdFirst:first course id
        :param slotFirst: slot to which first course id is assigned
        :param courseIdSecond: second course id
        :param slotSecond: slot to which second course id is assigned
        :return:
        """
        for cells in self.basicList:
            if (cells[0].courseId == courseIdFirst and cells[0].period == slotFirst \
                and cells[1].courseId == courseIdSecond and cells[1].period == slotSecond):
                return True
            elif (cells[1].courseId == courseIdFirst and cells[1].period == slotFirst \
                      and cells[0].courseId == courseIdSecond and cells[0].period == slotSecond):
                return True
        return False

    def checkPeriodIfInConstraints(self, firstCourseId, firstPeriod, secondCourseId, secondPeriod):
        """
        Check unavailable constraints for course

        :param firstCourseId:
        :param firstPeriod:
        :param secondCourseId:
        :param secondPeriod:
        :return:
        """
        if (secondCourseId is not []) and (firstPeriod in self.data.getConstraintsOnlyKeysForCourse(secondCourseId)):
            return False
        elif (firstCourseId is not []) and (secondPeriod in self.data.getConstraintsOnlyKeysForCourse(firstCourseId)):
            return False
        return True


    def simpleSwap(self, timetable, neighborhoodList, numberOfRooms):

        """
        Finds all possible swaps between courses or to empty position, create basicList structure

        :param timetable:
        :param neighborhoodList:
        :param numberOfRooms:
        """
        SIZE = len(timetable)

        for i in range(0, SIZE):

            for indexFirst in range(0, len(timetable[i])):
                cellFirst = timetable[i][indexFirst]

                for j in range(0, SIZE):
                    #Swap two courses
                    if j != i:
                        for indexSecond in filter(lambda x: self.data.getCourse(timetable[j][x][0]).typeOfRoom == \
                                self.data.getCourse(timetable[i][indexFirst][0]).typeOfRoom, range(0, len(timetable[j]))):

                            cellSecond = timetable[j][indexSecond]
                            if cellSecond[0] != cellFirst[0] and self.checkPeriodIfInConstraints(cellFirst[0], i, cellSecond[0], j):

                                if self.checkSimpleSwapMove(timetable, neighborhoodList, cellFirst[0], j) \
                                        & self.checkSimpleSwapMove(timetable, neighborhoodList, cellSecond[0], i):

                                    if self.checkIfNotInBasicNeighbourhood(cellFirst[0], i, cellSecond[0], j) is False:
                                        basicFirst = CellBasicNeighborhood(cellFirst[0], i, indexFirst)
                                        basicSecond = CellBasicNeighborhood(cellSecond[0], j, indexSecond)
                                        self.addCell(basicFirst, basicSecond)

                        #Swap (assign) course with empty position
                        if self.checkSimpleSwapMove(timetable, neighborhoodList, cellFirst[0], j) and len(timetable[j]) < numberOfRooms\
                            and self.checkPeriodIfInConstraints(cellFirst[0], i, [], j):
                            if self.checkIfNotInBasicNeighbourhood(cellFirst[0], i, [], j) is False:
                                basicFirst = CellBasicNeighborhood(cellFirst[0], i, indexFirst)
                                basicSecond = CellBasicNeighborhood([], j, [])
                                self.addCell(basicFirst, basicSecond)

    def getPossibleSwapsForCourse(self, courseId, slot):
        """
        Get all possible swaps for courseId - helper function for tests

        :param courseId:
        :param slot:
        :return:
        """
        listForCourse = []
        for x in self.basicList:
            if((x[0].courseId == courseId and x[0].period == slot) or (x[1].courseId == courseId and x[1].period == slot)):
                listForCourse.append(x)
        return listForCourse


def doSimpleSwap(timetable, (swap1, swap2)):
    """
    Perform simple swap

    :param timetable:
    :return:
    """
    newTimetable = {x: timetable[x][:] for x in timetable.keys()}
    if(swap2.index == []):
        newTimetable[swap2.period].append(newTimetable[swap1.period][swap1.index])
        del newTimetable[swap1.period][swap1.index]
    else:
        newTimetable[swap1.period][swap1.index], newTimetable[swap2.period][swap2.index] = \
            newTimetable[swap2.period][swap2.index], newTimetable[swap1.period][swap1.index]
    return newTimetable