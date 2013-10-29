from cats.utils.timetable import TimeTableFactory, CellOfTimeTable


CAPACITY_PENALTY = 1
MIN_WORKINGS_DAY_PENALTY = 5
COMPACTNESS_PENALTY = 2
STABILITY_PENALTY = 1

"""Count total penalty for soft constraints"""
def totalSoftConstraintsPenalty(partialTimetable, data, courseId, curriculumId):
    result = softConstraintsPenalty(partialTimetable, data, courseId, curriculumId)
    penalty = sum(result.values())
    return penalty



"""Count soft penalty for room capacity for course (roomIdList)"""
def penaltyRoomCapacity(data, courseId, roomIdList):

    dataCourse = data.getCourse(courseId)
    penalty = sum(filter(lambda x: x > 0, map(lambda x: dataCourse.studentsNum - data.getRoom(x).capacity, roomIdList)))
    penalty = CAPACITY_PENALTY * penalty
    return penalty

"""Count penalty for soft constraint curriculum compactness helper function"""
def countPenaltyForCurriculumCompactness(periodsList, periodsPerDay):
    penalty = 0
    for i in range(0, len(periodsList)):
        if i > 0 and periodsList[i - 1] + 1 == periodsList[i] and (periodsList[i - 1] / periodsPerDay == periodsList[i] / periodsPerDay):
            beforeLecture = True
        else:
            beforeLecture = False
        if i < len(periodsList) - 1 and (periodsList[i + 1] - 1 == periodsList[i]) and (periodsList[i + 1] / periodsPerDay == periodsList[i] / periodsPerDay):
            afterLecture = True
        else:
            afterLecture = False
        if beforeLecture is False and afterLecture is False:
            penalty += 1
    penalty = COMPACTNESS_PENALTY * penalty
    return penalty

"""Count soft penalty for minimum working days and room stability and curriculum compactness"""
def softConstraintsPenalty(partialTimetable, data, courseId, curriculumId = None):
    penaltyMinWorking = 0
    penaltyRoomStability = 0
    workingDaysSet = set()
    roomIdList = []
    curriculumPeriodsList = []
    totalNumberLectures = 0

    dataCourse = data.getCourse(courseId)

    for key in partialTimetable.keys():
        for cell in partialTimetable[key]:
            if cell.courseId == courseId:
                totalNumberLectures += 1
                workingDaysSet.add(key / data.periodsPerDay)
                roomIdList.append(cell.roomId)
            if curriculumId in cell.curriculumId:
                curriculumPeriodsList.append(key)
    """Room capacity penalty for one course and rooms list"""
    roomCapacityPenalty = penaltyRoomCapacity(data, courseId, roomIdList)

    """Minimum working days penalty"""
    workingDaysNumPartial = dataCourse.lectureNum - totalNumberLectures + len(workingDaysSet)
    if workingDaysNumPartial < dataCourse.minWorkingDays:
        penaltyMinWorking += MIN_WORKINGS_DAY_PENALTY * (dataCourse.minWorkingDays - workingDaysNumPartial)

    """Room stability penalty"""
    if len(set(roomIdList)) > 1:
        penaltyRoomStability += STABILITY_PENALTY * (len(set(roomIdList)) - 1)

    """Curriculum compactness penalty"""
    penaltyCurriculumCompactness = countPenaltyForCurriculumCompactness(curriculumPeriodsList, data.periodsPerDay)

    return {'penaltyMinWorkingDays': penaltyMinWorking, 'penaltyRoomStability': penaltyRoomStability,
            'penaltyCurriculumCompactness': penaltyCurriculumCompactness, 'penaltyRoomCapacity': roomCapacityPenalty}