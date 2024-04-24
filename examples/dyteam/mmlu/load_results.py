success_all = 0

with open('other_results.txt', 'r') as file:
    success, total = 0, 0
    for line in file:
        _, suc_cnt, total_cnt = line.strip().split(',')
        success += int(suc_cnt)
        total += int(total_cnt)
    print(f"other: {total}")
    success_all += success
    print(success / total)

with open('STEM_results.txt', 'r') as file:
    success, total = 0, 0
    for line in file:
        _, suc_cnt, total_cnt = line.strip().split(',')
        success += int(suc_cnt)
        total += int(total_cnt)
    print(f"STEM: {total}")
    success_all += success
    print(success / total)

with open('social_sciences_results.txt', 'r') as file:
    success, total = 0, 0
    for line in file:
        _, suc_cnt, total_cnt = line.strip().split(',')
        success += int(suc_cnt)
        total += int(total_cnt)
    print(f"social_sciences: {total}")
    success_all += success
    print(success / total)

with open('humanities_results.txt', 'r') as file:
    success, total = 0, 0
    for line in file:
        _, suc_cnt, total_cnt = line.strip().split(',')
        success += int(suc_cnt)
        total += int(total_cnt)
    print(f"humanities: {total}")
    success_all += success
    print(success / total)

print(f"success all:{success_all}")