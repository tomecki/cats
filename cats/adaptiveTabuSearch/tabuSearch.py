import operator
import signal
import threading
from cats.adaptiveTabuSearch import perturbation
from cats.adaptiveTabuSearch.heuristics import initialSolution
from cats.adaptiveTabuSearch.advancedNeighborhood import AdvancedNeighborhood, doKempeSwap
from cats.adaptiveTabuSearch.tabuLists import TabuList, AdvancedTabuList
from cats.adaptiveTabuSearch import softConstraints2
from cats.adaptiveTabuSearch.basicNeighborhood import BasicNeighborhood, doSimpleSwap
import time
from cats.utils.timetable import TimeTable, TimeTableFactory

"""Tabu search algorithm"""
"""Period related costs - sum(minimumWorkingDays, curriculumCompactness)"""
"""Room related costs - sum(roomCapacity, roomStability)"""

INITIAL_TABU_DEPTH = 10
INITIAL_PERTURBATION_STRENGTH = 4
MAX_PERTURBATION_STRENGTH = 15
LAMBDA = 0.3
INITIAL_ITERATIONS_WITHOUT_CHANGE = 2
INITIAL_INTENSIFICATION_ITERATIONS = 2




class AdaptiveTabuSearch:
    def __init__(self, data, timeLimit):
        self.data = data
        self.timeLimit = timeLimit
        self.bestSolution = TimeTableFactory.getTimeTable(self.data)
        self.lock = threading.Lock()

    def signal_handler(self):
        raise Exception()

    def run(self):
        signal.signal(signal.SIGALRM, self.signal_handler)
        signal.alarm(self.timeLimit)
        try:
            self.runTimeLimited()
        finally:
            return self.bestSolution


    def updateBest(self, better):
        with self.lock:
            self.bestSolution = better.copy()


        def runTimeLimited(self):
            initialSolution(self.bestSolution, self.data)
            # print "INITIALSOLUTION", softConstraints2.totalSoftConstraintsForTimetable(timetable.getTimeTable(), data)
            xi = 0
            mju = 0.6
            theta = INITIAL_TABU_DEPTH
            eta = INITIAL_PERTURBATION_STRENGTH
            solution = tabuSearch(self.bestSolution, self.data, theta)
            solutionQuality = softConstraints2.totalSoftConstraintsForTimetable(solution.getTimeTable(), self.data)
            bestQuality = solutionQuality
            self.updateBest(solution)
            iterationsWithoutChange = INITIAL_ITERATIONS_WITHOUT_CHANGE
            while iterationsWithoutChange>0:
                print "ATS:", solutionQuality, bestQuality
                # print "THETA: %f ETA: %f xi: %f F: %f" % (theta, eta, xi, softConstraints2.totalSoftConstraintsForTimetable(bestSolution.getTimeTable(), data))
                perturbedSolution = perturbation.produceRandomlySimpleOrKempeSwap(solution, self.data,  eta, 30)
                perturbedTabu = tabuSearch(perturbedSolution, self.data, theta)

                perturbedQuality = softConstraints2.totalSoftConstraintsForTimetable(perturbedTabu.getTimeTable(), self.data)
                perturbedTabuQuality = softConstraints2.totalSoftConstraintsForTimetable(solution.getTimeTable(), self.data)
                solutionQuality = softConstraints2.totalSoftConstraintsForTimetable(solution.getTimeTable(), self.data)

                # print "PERTURBED", perturbedQuality, "PERTURBED_TABU", perturbedTabuQuality, "SOLUTION", solutionQuality

                if perturbedTabuQuality <= solutionQuality+2:
                    intensification = INITIAL_INTENSIFICATION_ITERATIONS
                    while intensification>0:
                        # print "RESTARTING", "PERTURBEDTABU", perturbedTabuQuality, "SOLUTION", solutionQuality
                        intensification -= 1
                        theta = (1+mju)*theta
                        perturbedTabuQuality = softConstraints2.totalSoftConstraintsForTimetable(perturbedSolution.getTimeTable(), self.data)
                        perturbedTabu = tabuSearch(perturbedTabu, self.data, theta)

                        if perturbedTabuQuality<=softConstraints2.totalSoftConstraintsForTimetable(perturbedTabu.getTimeTable(), self.data):
                            break
                if softConstraints2.totalSoftConstraintsForTimetable(perturbedTabu.getTimeTable(), self.data) < \
                    softConstraints2.totalSoftConstraintsForTimetable(solution.getTimeTable(), self.data):
                    solution = perturbedTabu.copy()
                    theta = INITIAL_TABU_DEPTH
                    eta = INITIAL_PERTURBATION_STRENGTH
                    iterationsWithoutChange = INITIAL_ITERATIONS_WITHOUT_CHANGE
                else:
                    theta = INITIAL_TABU_DEPTH
                    xi+=1
                    eta = max(INITIAL_PERTURBATION_STRENGTH+LAMBDA*xi, MAX_PERTURBATION_STRENGTH)
                    iterationsWithoutChange -=1
                solutionQuality = softConstraints2.totalSoftConstraintsForTimetable(solution.getTimeTable(), self.data)
                if  solutionQuality < bestQuality:
                    bestQuality = solutionQuality
                    self.updateBest(solution)
            return self.bestSolution







def tabuSimpleNeighborhood(timetable, data, theta):

    initialSolution = timetable.copy()

    tabuList = TabuList(data.getAllCourses(), initialSolution.neighbourhoodList)
    b = BasicNeighborhood(data)
    currentBestSolution = initialSolution.getTimeTable()
    currentBestQuality = softConstraints2.totalSoftConstraintsForTimetable(initialSolution.getTimeTable(), data)
    #print "SIMPLE TABU", currentBestQuality, "THETA:", theta

    for i in xrange(theta):
        b.clearBasicList()

        b.simpleSwap(initialSolution.getTimeTable(), initialSolution.neighbourhoodList, len(data.getAllRooms()))
        tabuTenure = {x.id : tabuList.tabuTenure(x.id, initialSolution.getTimeTable(), data) for x in data.getAllCourses()}

        neighborhood = filter(lambda swap: \
            (swap[0].courseId==[] or
                tabuList.isTabuMove(\
                    swap[0].courseId, \
                    swap[0].period, \
                    initialSolution.getTimeTable()[swap[0].period][swap[0].index][1], \
                    i, \
                    tabuTenure[swap[0].courseId]) == False)
                and (swap[1].courseId==[] or \
                tabuList.isTabuMove( \
                    swap[1].courseId, \
                    swap[1].period, \
                    initialSolution.getTimeTable()[swap[1].period][swap[1].index][1],
                    i,\
                    tabuTenure[swap[1].courseId]) == False), \
                b.getBasicList())

        if len(neighborhood)==0:
            break

        candidates = map(lambda x: (x, doSimpleSwap(initialSolution.getTimeTable(), x)), neighborhood)
        initialQuality = softConstraints2.totalSoftConstraintsForTimetable(initialSolution.getTimeTable(), data)
        print currentBestQuality, initialQuality, len(neighborhood)

        candidatesAfterPeriods = map(lambda x:  (x,  softConstraints2.totalSoftConstraintsForTimetable(x[1], data)), candidates)

        bestSwap = sorted(candidatesAfterPeriods, key=lambda x: x[1])[0]
        (first, second) = bestSwap[0][0]

        if first.courseId!=[]:
            tabuList.addTabuMove(first.courseId, first.period, initialSolution.getTimeTable()[first.period][first.index][1], i)
        if second.courseId!=[]:
            tabuList.addTabuMove(second.courseId, second.period, initialSolution.getTimeTable()[second.period][second.index][1], i)

        initialSolution.timeTable = bestSwap[0][1]
        if bestSwap[1]<currentBestQuality:
            currentBestQuality, currentBestSolution = bestSwap[1], bestSwap[0][1]

    initialSolution.timeTable = currentBestSolution


    sortedRoomIdList = sorted(data.getAllRooms(), key=lambda room: room.capacity, reverse=True)
    for x in currentBestSolution.keys():
        currentBestSolution[x] = matchingRoomAllocations(currentBestSolution, x, data, sortedRoomIdList)

    print "SIMPLE TABU END:", softConstraints2.totalSoftConstraintsForTimetable(currentBestSolution, data)

    initialSolution.timeTable = currentBestSolution
    return initialSolution




def tabuAdvancedNeighborhood(timetable, data, theta):

    initialSolution = timetable.copy()

    tabuList = AdvancedTabuList(data.getAllCourses(), initialSolution.neighbourhoodList)
    b= AdvancedNeighborhood()
    currentBestSolution = initialSolution.getTimeTable()
    currentBestQuality = softConstraints2.totalSoftConstraintsForTimetable(initialSolution.getTimeTable(), data)
    #print "ADVANCED", currentBestQuality, "THETA", theta

    for i in xrange(theta):

        tabuTenure = {x.id : tabuList.tabuTenure(x.id, initialSolution.getTimeTable(), data) for x in data.getAllCourses()}

        neighborhood = filter(lambda x: \
            any(map(lambda y: tabuList.isTabuMove(y[0], x[1]["moves"][0][0], i, tabuTenure[y[0]]), x[1]["moves"][0][1]))==False and \
            any(map(lambda y: tabuList.isTabuMove(y[0], x[1]["moves"][1][0], i, tabuTenure[y[0]]), x[1]["moves"][0][1]))==False,
            b.exploreNeighborhood(initialSolution, data))

        candidates = map(lambda x: doKempeSwap(x, initialSolution.getTimeTable()), neighborhood)
        candidates = sorted(map(lambda x: (x, softConstraints2.totalSoftConstraintsForTimetable(x, data)), candidates), key=lambda x: x[1])

        bestCandidate, bestCandidateQuality = candidates[0]

        initialSolution.timeTable = {x: bestCandidate[x][:] for x in bestCandidate.keys()}
        print bestCandidateQuality, currentBestQuality ,len(neighborhood)

        if bestCandidateQuality<currentBestQuality:
            currentBestSolution = {x: bestCandidate[x][:] for x in bestCandidate.keys()}
            currentBestQuality = bestCandidateQuality
            #print softConstraints2.totalSoftConstraintsForTimetable(currentBestSolution, data), bestCandidateQuality


    sortedRoomIdList = sorted(data.getAllRooms(), key=lambda room: room.capacity, reverse=True)
    for x in currentBestSolution.keys():
        currentBestSolution[x] = matchingRoomAllocations(currentBestSolution, x, data, sortedRoomIdList)




    initialSolution.timeTable = {x: currentBestSolution[x][:] for x in currentBestSolution.keys()}
    print "ADVANCED TABU END:", softConstraints2.totalSoftConstraintsForTimetable(currentBestSolution, data)



    return initialSolution


def tabuSearch(initialSolution, data, theta):
    improved = True
    bestSolution= initialSolution.copy()
    bestQuality = softConstraints2.totalSoftConstraintsForTimetable(bestSolution.getTimeTable(), data)
    iterations = INITIAL_ITERATIONS_WITHOUT_CHANGE
    while iterations>0:
        simpleNeighborhood = tabuSimpleNeighborhood(initialSolution.copy(), data, int(theta))

        advancedNeighborhood = tabuAdvancedNeighborhood(simpleNeighborhood.copy(), data, int(theta)/3)
        advancedQuality = softConstraints2.totalSoftConstraintsForTimetable(advancedNeighborhood.getTimeTable(), data)
        if advancedQuality < bestQuality:
            iterations = INITIAL_ITERATIONS_WITHOUT_CHANGE
            bestSolution = advancedNeighborhood.copy()
            bestQuality = advancedQuality
        else:
            iterations -=1
        initialSolution = advancedNeighborhood.copy()
    print "TABU", bestQuality, "DEPTH", theta
    return bestSolution



def matchingRoomAllocations(timetable, slot, data, sortedRoomIdList):
    """
    Matching algorithm to make room allocations (number of courses in slot <= number of rooms)
    Match rooms to courses starting from courses with the biggest number of students, match the biggest available room
    :param timetable: timetable to which assigned rooms ids
    :param slot: slot to which assign rooms
    :param data: data to tested example
    :param sortedRoomIdList: sorted list of rooms regarding to capacity
    :return: timetable for slot with assigned rooms for each course
    """
    studentsForCourse= {x[0]: data.getCourse(x[0]).studentsNum for x in timetable[slot]}
    sortedStudentsForCourse = sorted(studentsForCourse.iteritems(), key=operator.itemgetter(1), reverse=True)
    size = len(timetable[slot])
    for i in range(0, size):
        indexOfRoom = map(operator.itemgetter(0), sortedStudentsForCourse).index(timetable[slot][i][0])
        # modify room Id
        tuple = timetable[slot][i]
        timetable[slot][i] = (tuple[0], sortedRoomIdList[indexOfRoom].id)

    return timetable[slot]







