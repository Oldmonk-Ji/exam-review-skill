---
title: "DASE7501 Robot Modelling, Planning and Control --- Focus Paper (Lectures 1, 2 & 4)"
subtitle: "Modelled on Homework 1 and past-exam styles · 20 questions · 100 marks · Suggested time 60 minutes"
fontsize: 10.5pt
documentclass: ctexart
geometry: margin=2.1cm
colorlinks: true
header-includes: |
  \setlength{\emergencystretch}{3em}
  \linespread{1.2}
  \setlength{\tabcolsep}{3pt}
  \renewcommand{\arraystretch}{1.05}
  \widowpenalty=10000
  \clubpenalty=10000
  \brokenpenalty=10000
  \usepackage{amsmath}
  \usepackage{amssymb}
  \usepackage{booktabs}
  \usepackage{enumitem}
  \setlist[enumerate]{nosep}
  \usepackage{tikz}
  \usetikzlibrary{calc,positioning}
  \usepackage{tcolorbox}
  \tcbuselibrary{skins,breakable}
  \renewenvironment{quote}{\begin{tcolorbox}[colback=blue!3!white,colframe=blue!40!black,boxrule=0.4pt,arc=1.5mm,breakable,left=2mm,right=2mm,top=1mm,bottom=1mm]}{\end{tcolorbox}}
  \setCJKmainfont{SimSun}
  \setCJKsansfont{Microsoft YaHei}
mainfont: "Times New Roman"
sansfont: "Microsoft YaHei"
monofont: "Consolas"
---

# Part 1: Questions

**Instructions**: This focus paper covers the examinable points of Lectures 1, 2 and 4, and is modelled on Homework 1 and the question styles tested in past exams (applications, DOF, robot selection, accuracy/repeatability, sensitivity, PWM). It is written in English, exactly like the real exam. Answer ALL questions first; only when you finish should you open Part 2 (Answer Key and Solutions), which is at the end of this document. No Chinese annotations appear in this part.

**Time suggestion**: 60 minutes. **Total**: 100 marks.

## Section A: Multiple Choice (10 questions, 2 marks each, 20 marks)

**Q1.** Which of the following is NOT a typical application of industrial robots in manufacturing and logistics?

A. Welding

B. Painting

C. Assembly

D. Cooking meals in a restaurant kitchen

**Q2.** To polish a free-form surface, the minimum number of degrees of freedom (DOF) that a robot must have is:

A. 3

B. 4

C. 5

D. 6

**Q3.** A SCARA robot has three revolute joints with parallel vertical axes and one prismatic joint that moves vertically. Its number of DOF is:

A. 3

B. 4

C. 5

D. 6

**Q4.** Which robot type is best suited for handling very large parts and moving material over long distances?

A. SCARA

B. Delta (parallel)

C. Gantry

D. Articulated

**Q5.** A robot returns to the same taught point within $\pm 0.02$ mm every time, but that point is about 2 mm away from the commanded position. This robot has:

A. Good accuracy and good repeatability

B. Good accuracy but poor repeatability

C. Poor accuracy but good repeatability

D. Poor accuracy and poor repeatability

**Q6.** According to the lecture, which factor affects accuracy but does NOT affect repeatability?

A. Temperature

B. Payload

C. Calibration

D. Wear-out

**Q7.** Which of the following sensors gives a digital output signal?

A. Resolver

B. Potentiometer

C. Optical encoder

D. LVDT

**Q8.** For a DC motor, the speed is mainly controlled by ____, and the direction of rotation is determined by ____.

A. the frequency; the duty cycle

B. the supplied voltage; the polarity of the supplied voltage

C. the duty cycle; the frequency

D. the motor current; the temperature

**Q9.** The pulse-width ratio (duty cycle) of a PWM signal is defined as:

A. $t_{period} / t_{on}$

B. $t_{on} / t_{period}$

C. $V_{high} / V_{low}$

D. $f \times t_{on}$

**Q10.** A robot must transfer a 15 kg pack of water bottles to a pallet. Which specification is the hard constraint that immediately rules out a small table-top robot?

A. Payload, with a margin for the gripper

B. Repeatability better than 0.001 mm

C. Tool speed faster than 10 m/s

D. More than 10 DOF

## Section B: True/False (4 questions, 2 marks each, 8 marks)

Write T (True) or F (False) for each statement.

**Q11.** In PWM control of a DC motor, the supplied voltage is varied continuously to change the motor speed.

**Q12.** The H-bridge in a DC motor driver determines the direction of the motor current.

**Q13.** Wear-out of the transmission affects the repeatability of a robot but not its accuracy.

**Q14.** The sensitivity of a sensor is the ratio of the change in output to the change in input.

## Section C: Calculation (4 questions, 10 marks each, 40 marks)

**Q15.** A robot is programmed to move to a tool position $(100, 200, 0)$ several times. A laser scanner measures the tool position and obtains the following results (unit: mm):

$$(95, 203, 3),\quad (97, 205, 5),\quad (94, 207, 4),\quad (96, 206, 2),\quad (93, 204, 1)$$

Compute the accuracy and the repeatability of the robot.

**Q16.** A pressure sensor is calibrated by applying known pressures, with the following results:

| Pressure $P$ (kPa) | 0 | 5 | 10 | 15 | 20 |
|---|---|---|---|---|---|
| Output $V$ (mV) | 0 | 4 | 8 | 12 | 16 |

(a) Determine the sensitivity of the sensor.

(b) Estimate the output voltage when the applied pressure is 12.5 kPa.

**Q17.** A 24 V DC supply drives a motor through a PWM amplifier whose switching frequency is 20 kHz.

(a) What is the average voltage applied to the motor when the duty cycle $D = 0.25$?

(b) What duty cycle is needed to obtain an average voltage of about 18 V?

(c) What is the switching period, and for how long is the switch ON within one period when $D = 0.25$?

**Q18.** A sensor has a sensitivity error of $\pm 0.1\%$ of the reading per °C change in temperature. At 20°C it outputs 4.00 V. Estimate the range of the output at 30°C, assuming the sensitivity error is the only source of error.

## Section D: Short Answer (2 questions, 32 marks)

**Q19.** (12 marks) List at least six applications of industrial robots in manufacturing and logistics.

**Q20.** (20 marks) A pack of water bottles weighs 15 kg. The pack is transferred to a pallet, and the maximum distance between the pack and the pallet is 2 meters. What do you need to consider when selecting a robot for this task? Give details and reasons.

# Part 2: Answer Key and Solutions 答案解析

**Quick key (速查)**: 1-D, 2-C, 3-B, 4-C, 5-C, 6-C, 7-C, 8-B, 9-B, 10-A; 11-F, 12-T, 13-T, 14-T; 15: accuracy $\approx$ 7.98 mm, repeatability $\approx$ 2.40 mm; 16: (a) 0.8 mV/kPa, (b) 10 mV; 17: (a) 6 V, (b) 0.75, (c) 50 µs, 12.5 µs; 18: 3.96--4.04 V.

**Section A (选择题详解)**:

**Q1. D.** 焊接(welding)、喷涂(painting)、装配(assembly)、拾取与放置(pick and place)、产品检测(product inspection)、测试(testing)、抛光打磨(polishing/grinding)、码垛(palletizing)、上下料(loading/unloading)、分拣(sorting)等都是讲义列出的典型应用;餐厅做饭不是典型工业机器人应用。

**Q2. C.** 抛光自由曲面时,工具需要 3 个自由度到达表面任意点(定位),再用 2 个自由度把工具轴线调成与表面垂直(定向);绕工具自身轴线的旋转(roll)不改变抛光接触,所以最少 5 个自由度。实际中通常使用 6 自由度关节型机器人(更通用,可达任意姿态)。

**Q3. B.** SCARA 有 3 个旋转关节(轴线互相平行且竖直)+ 1 个竖直移动的棱柱关节 = 4 DOF。讲义:SCARA 最少 4 轴,竖直运动平滑快速,水平面内高顺应性(high compliance in the horizontal plane),重复性 < 0.03 mm,适合精密高速轻型装配。

**Q4. C.** 龙门机器人(gantry)工作空间非常大(very large working envelope)、负载 10--1000 kg,典型应用就是搬运超大件、长距离输送物料;缺点是负载大时速度慢。关节型(articulated)负载可达 1--2000 kg 且速度快,但工作空间是“相对体积大”而非绝对最大;SCARA 与 Delta 用于小型高速场合,负载轻。

**Q5. C.** 每次回到同一示教点 $\pm 0.02$ mm,说明重复性(repeatability)很好;但整体离指令位置差 2 mm,说明精度(accuracy)差。精度相对指令位置(commanded position),重复性相对记录/示教位置(recorded/taught position)。好重复性 + 差精度意味着系统性偏移(systematic offset),应检查标定(calibration)与机器人模型(robot model)。

**Q6. C.** 影响精度的因素:标定(calibration)、机器人模型(robot model)、运动控制(motion control)、温度、负载、速度。影响重复性的因素:温度、负载、速度、磨损(wear-out)、运动控制。标定与机器人模型只影响精度;磨损只影响重复性。

**Q7. C.** 光学编码器(optical encoder)输出数字量(digital signal),精度 < 1 角分;旋转变压器(resolver)输出模拟量(analog signal,精度 > 2 角分);电位计(potentiometer)与 LVDT 也都是模拟输出。

**Q8. B.** 讲义原话:电机转速由供电电压(supplied voltage)决定,转向由供电电压极性(polarity)决定。PWM 调节的是平均电压(等效供电电压);H 桥决定电流方向;电流环近似控制转矩(torque),PID 再闭环修正速度/位置。

**Q9. B.** 占空比(pulse-width ratio)$D = t_{on} / t_{period}$。PWM 不改变供电电压幅值,而是以高频(如 20 kHz)通断,理想平均电压约为 $D \times V_{supply}$。

**Q10. A.** 15 kg 的整包水加夹爪自重与安全裕量,负载(payload)至少要 15--20 kg,直接排除小型桌面机器人;其次看工作空间(最大距离 2 m,臂展必须覆盖)与重复性(码放到位)。B、C、D 的要求都不必要(0.001 mm、10 m/s、10 DOF 均远超需求)。

**Section B (判断题详解)**:

**Q11. F.** PWM 恰恰不连续改变供电电压:电压幅值保持不变,以一定脉冲比高速通断,电机只“看到”平均效果,理想平均电压 $V_{avg} \approx D \times V_{supply}$。

**Q12. T.** H 桥通过导通不同的开关组合改变流过电机的电流方向,从而控制转向;PWM 调节平均电压控制转速;PID 对速度/位置环做闭环修正。

**Q13. T.** 磨损(wear-out)在重复性的影响因素里,不在精度的影响因素里:传动磨损使每次到达同一示教点的散布变大(重复性变差),但不改变系统整体的目标偏差(精度)。

**Q14. T.** 灵敏度(sensitivity)是输出变化与输入变化之比(output/input)。例:热电偶灵敏度 20 mV/°C,温度每变化 1°C 输出变化 20 mV。

**Section C (计算题详解)**:

> **【Q15 详解】**
>
> 指令位置(commanded position)$(X_c, Y_c, Z_c) = (100, 200, 0)$。RIA 公式:先求每点相对指令点的误差距离(偏差平方和再开方),再取平均。
>
> 点 1 $(95, 203, 3)$:偏差 $(-5, 3, 3)$,$25 + 9 + 9 = 43$,$\sqrt{43} \approx 6.56$ mm
>
> 点 2 $(97, 205, 5)$:偏差 $(-3, 5, 5)$,$9 + 25 + 25 = 59$,$\sqrt{59} \approx 7.68$ mm
>
> 点 3 $(94, 207, 4)$:偏差 $(-6, 7, 4)$,$36 + 49 + 16 = 101$,$\sqrt{101} \approx 10.05$ mm
>
> 点 4 $(96, 206, 2)$:偏差 $(-4, 6, 2)$,$16 + 36 + 4 = 56$,$\sqrt{56} \approx 7.48$ mm
>
> 点 5 $(93, 204, 1)$:偏差 $(-7, 4, 1)$,$49 + 16 + 1 = 66$,$\sqrt{66} \approx 8.12$ mm
>
> $$\text{Accuracy} = \frac{6.56 + 7.68 + 10.05 + 7.48 + 8.12}{5} \approx \frac{39.90}{5} \approx 7.98\ \text{mm}$$
>
> 重复性:均值 $\bar{X} = (95+97+94+96+93)/5 = 95$,$\bar{Y} = (203+205+207+206+204)/5 = 205$,$\bar{Z} = (3+5+4+2+1)/5 = 3$。每点相对均值的距离:
>
> 点 1 $(0, -2, 0)$:$\sqrt{4} = 2.00$ mm;点 2 $(2, 0, 2)$:$\sqrt{8} \approx 2.83$ mm;点 3 $(-1, 2, 1)$:$\sqrt{6} \approx 2.45$ mm;点 4 $(1, 1, -1)$:$\sqrt{3} \approx 1.73$ mm;点 5 $(-2, -1, -2)$:$\sqrt{9} = 3.00$ mm
>
> $$\text{Repeatability} = \frac{2.00 + 2.83 + 2.45 + 1.73 + 3.00}{5} \approx \frac{12.01}{5} \approx 2.40\ \text{mm}$$
>
> 结论:精度约 7.98 mm,重复性约 2.40 mm。精度差于重复性,说明机器人整体偏离目标较远(可能有标定/模型误差),但每次落点相对集中。

> **【Q16 详解】**
>
> (a) 灵敏度(sensitivity)= 输出变化 / 输入变化。任取相邻两点:$\Delta V = 4$ mV,$\Delta P = 5$ kPa,
>
> $$S = \frac{\Delta V}{\Delta P} = \frac{4\ \text{mV}}{5\ \text{kPa}} = 0.8\ \text{mV/kPa}$$
>
> (b) 数据过原点且线性,$V = 0.8 \times P$。当 $P = 12.5$ kPa 时,$V = 0.8 \times 12.5 = 10$ mV。

> **【Q17 详解】**
>
> (a) 理想平均电压约为占空比乘电源电压:
>
> $$V_{avg} \approx D \times V_{supply} = 0.25 \times 24 = 6\ \text{V}$$
>
> (b) 要求 $V_{avg} = 18$ V,则 $D = 18 / 24 = 0.75$。
>
> (c) 开关周期 $T = 1/f = 1/20\,000 = 50\ \mu s$;导通时间 $t_{on} = D \times T = 0.25 \times 50 = 12.5\ \mu s$。

> **【Q18 详解】**
>
> 温度变化 $\Delta T = 30 - 20 = 10$ °C;灵敏度误差为读数每变化 1°C 有 $\pm 0.1\%$,故总误差 $= \pm 0.1\% \times 10 = \pm 1\%$。
>
> $$4.00 \times (\pm 1\%) = \pm 0.04\ \text{V}$$
>
> 输出范围:$4.00 - 0.04 = 3.96$ V 到 $4.00 + 0.04 = 4.04$ V,即 3.96--4.04 V。

**Section D (简答题详解)**:

> **【Q19 详解】**
>
> 任写六个即满分:焊接(welding)、喷涂(painting)、装配(assembly)、拾取与放置(pick and place)、产品检测(product inspection)、测试(testing)、抛光/打磨/去毛刺(polishing/grinding/deburring)、机加工(machining)、码垛(palletizing)、上下料(loading/unloading)、包装(packaging)、分拣(sorting)、仓储物流(warehouse logistics,AGV/移动机器人搬运)等。

> **【Q20 详解】**
>
> 核心考虑(给出理由):
>
> 1. **负载(Payload)**:水包 15 kg,还要加上夹爪/吸盘自重与安全裕量,机器人负载至少要 15--20 kg,直接排除小型机器人;
> 2. **工作空间/臂展(Workspace/reach)**:最大搬运距离 2 m,机器人臂展(reach)必须覆盖 2 m 及托盘区域,否则够不到;
> 3. **自由度(DOF)**:码放需要定位加姿态调整,至少 4 DOF(3 个定位 + 1 个竖直/旋转),常用 6 自由度关节型;
> 4. **重复性(Repeatability)**:要准确码放到托盘上,重复性通常要求 0.1 mm 量级或更好;
> 5. **速度/节拍(Speed/cycle time)**:决定单位时间码放数量,影响生产效率;
> 6. **结构类型(Structure)**:6 轴关节型(灵活、臂展大)或龙门机(大工作空间、重负载)合适;SCARA/Delta 适合轻载高速场合;
> 7. **末端执行器(End-effector)**:夹爪或真空吸盘要适配整包水瓶,其自重计入负载;
> 8. **环境与安全(Environment and safety)**:车间有水汽需防护等级(IP rating);人机共处需围栏或协作安全措施;
> 9. **其他**:成本、控制器与编程方式(示教 vs 离线编程)、供电与占地。
