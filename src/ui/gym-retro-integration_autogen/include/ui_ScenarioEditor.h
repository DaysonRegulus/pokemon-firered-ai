/********************************************************************************
** Form generated from reading UI file 'ScenarioEditor.ui'
**
** Created by: Qt User Interface Compiler version 5.15.3
**
** WARNING! All changes made in this file will be lost when recompiling UI file!
********************************************************************************/

#ifndef UI_SCENARIOEDITOR_H
#define UI_SCENARIOEDITOR_H

#include <QtCore/QVariant>
#include <QtWidgets/QApplication>
#include <QtWidgets/QCheckBox>
#include <QtWidgets/QComboBox>
#include <QtWidgets/QDialog>
#include <QtWidgets/QDialogButtonBox>
#include <QtWidgets/QFrame>
#include <QtWidgets/QGridLayout>
#include <QtWidgets/QHBoxLayout>
#include <QtWidgets/QLabel>
#include <QtWidgets/QLineEdit>
#include <QtWidgets/QPushButton>
#include <QtWidgets/QScrollArea>
#include <QtWidgets/QSpacerItem>
#include <QtWidgets/QSpinBox>
#include <QtWidgets/QStackedWidget>
#include <QtWidgets/QVBoxLayout>
#include <QtWidgets/QWidget>

QT_BEGIN_NAMESPACE

class Ui_ScenarioEditor
{
public:
    QGridLayout *gridLayout;
    QHBoxLayout *horizontalLayout;
    QComboBox *rewardFunc;
    QCheckBox *rewardFuncUse;
    QSpacerItem *horizontalSpacer;
    QLabel *label;
    QSpinBox *playerId;
    QComboBox *variableName;
    QLineEdit *doneNodeName;
    QFrame *line;
    QDialogButtonBox *buttonBox;
    QPushButton *addDone;
    QPushButton *reloadScripts;
    QPushButton *addReward;
    QPushButton *addDoneNode;
    QPushButton *guess;
    QPushButton *loadScript;
    QFrame *line_2;
    QHBoxLayout *horizontalLayout_2;
    QComboBox *doneFunc;
    QCheckBox *doneFuncUse;
    QSpacerItem *horizontalSpacer_2;
    QScrollArea *scrollArea;
    QWidget *reward;
    QVBoxLayout *verticalLayout;
    QStackedWidget *rewardList;
    QScrollArea *scrollArea_2;
    QWidget *doneList;
    QVBoxLayout *verticalLayout_2;

    void setupUi(QDialog *ScenarioEditor)
    {
        if (ScenarioEditor->objectName().isEmpty())
            ScenarioEditor->setObjectName(QString::fromUtf8("ScenarioEditor"));
        ScenarioEditor->resize(985, 600);
        QSizePolicy sizePolicy(QSizePolicy::Fixed, QSizePolicy::Fixed);
        sizePolicy.setHorizontalStretch(0);
        sizePolicy.setVerticalStretch(0);
        sizePolicy.setHeightForWidth(ScenarioEditor->sizePolicy().hasHeightForWidth());
        ScenarioEditor->setSizePolicy(sizePolicy);
        gridLayout = new QGridLayout(ScenarioEditor);
        gridLayout->setObjectName(QString::fromUtf8("gridLayout"));
        gridLayout->setContentsMargins(-1, -1, -1, 0);
        horizontalLayout = new QHBoxLayout();
        horizontalLayout->setSpacing(12);
        horizontalLayout->setObjectName(QString::fromUtf8("horizontalLayout"));
        rewardFunc = new QComboBox(ScenarioEditor);
        rewardFunc->setObjectName(QString::fromUtf8("rewardFunc"));
        rewardFunc->setEnabled(false);

        horizontalLayout->addWidget(rewardFunc);

        rewardFuncUse = new QCheckBox(ScenarioEditor);
        rewardFuncUse->setObjectName(QString::fromUtf8("rewardFuncUse"));
        sizePolicy.setHeightForWidth(rewardFuncUse->sizePolicy().hasHeightForWidth());
        rewardFuncUse->setSizePolicy(sizePolicy);

        horizontalLayout->addWidget(rewardFuncUse);

        horizontalSpacer = new QSpacerItem(40, 20, QSizePolicy::Expanding, QSizePolicy::Minimum);

        horizontalLayout->addItem(horizontalSpacer);

        label = new QLabel(ScenarioEditor);
        label->setObjectName(QString::fromUtf8("label"));

        horizontalLayout->addWidget(label);

        playerId = new QSpinBox(ScenarioEditor);
        playerId->setObjectName(QString::fromUtf8("playerId"));
        playerId->setWrapping(true);
        playerId->setMinimum(1);
        playerId->setMaximum(2);

        horizontalLayout->addWidget(playerId);


        gridLayout->addLayout(horizontalLayout, 0, 0, 1, 6);

        variableName = new QComboBox(ScenarioEditor);
        variableName->setObjectName(QString::fromUtf8("variableName"));

        gridLayout->addWidget(variableName, 7, 0, 1, 2);

        doneNodeName = new QLineEdit(ScenarioEditor);
        doneNodeName->setObjectName(QString::fromUtf8("doneNodeName"));

        gridLayout->addWidget(doneNodeName, 8, 0, 1, 2);

        line = new QFrame(ScenarioEditor);
        line->setObjectName(QString::fromUtf8("line"));
        line->setFrameShape(QFrame::HLine);
        line->setFrameShadow(QFrame::Sunken);

        gridLayout->addWidget(line, 2, 0, 1, 6);

        buttonBox = new QDialogButtonBox(ScenarioEditor);
        buttonBox->setObjectName(QString::fromUtf8("buttonBox"));
        buttonBox->setOrientation(Qt::Horizontal);
        buttonBox->setStandardButtons(QDialogButtonBox::Cancel|QDialogButtonBox::Ok|QDialogButtonBox::Save);

        gridLayout->addWidget(buttonBox, 10, 0, 1, 6);

        addDone = new QPushButton(ScenarioEditor);
        addDone->setObjectName(QString::fromUtf8("addDone"));

        gridLayout->addWidget(addDone, 7, 3, 1, 1);

        reloadScripts = new QPushButton(ScenarioEditor);
        reloadScripts->setObjectName(QString::fromUtf8("reloadScripts"));

        gridLayout->addWidget(reloadScripts, 8, 5, 1, 1);

        addReward = new QPushButton(ScenarioEditor);
        addReward->setObjectName(QString::fromUtf8("addReward"));

        gridLayout->addWidget(addReward, 7, 2, 1, 1);

        addDoneNode = new QPushButton(ScenarioEditor);
        addDoneNode->setObjectName(QString::fromUtf8("addDoneNode"));

        gridLayout->addWidget(addDoneNode, 8, 2, 1, 1);

        guess = new QPushButton(ScenarioEditor);
        guess->setObjectName(QString::fromUtf8("guess"));

        gridLayout->addWidget(guess, 8, 3, 1, 1);

        loadScript = new QPushButton(ScenarioEditor);
        loadScript->setObjectName(QString::fromUtf8("loadScript"));

        gridLayout->addWidget(loadScript, 7, 5, 1, 1);

        line_2 = new QFrame(ScenarioEditor);
        line_2->setObjectName(QString::fromUtf8("line_2"));
        line_2->setFrameShape(QFrame::VLine);
        line_2->setFrameShadow(QFrame::Sunken);

        gridLayout->addWidget(line_2, 7, 4, 2, 1);

        horizontalLayout_2 = new QHBoxLayout();
        horizontalLayout_2->setSpacing(12);
        horizontalLayout_2->setObjectName(QString::fromUtf8("horizontalLayout_2"));
        doneFunc = new QComboBox(ScenarioEditor);
        doneFunc->setObjectName(QString::fromUtf8("doneFunc"));
        doneFunc->setEnabled(false);

        horizontalLayout_2->addWidget(doneFunc);

        doneFuncUse = new QCheckBox(ScenarioEditor);
        doneFuncUse->setObjectName(QString::fromUtf8("doneFuncUse"));
        sizePolicy.setHeightForWidth(doneFuncUse->sizePolicy().hasHeightForWidth());
        doneFuncUse->setSizePolicy(sizePolicy);

        horizontalLayout_2->addWidget(doneFuncUse);

        horizontalSpacer_2 = new QSpacerItem(40, 20, QSizePolicy::Expanding, QSizePolicy::Minimum);

        horizontalLayout_2->addItem(horizontalSpacer_2);


        gridLayout->addLayout(horizontalLayout_2, 3, 0, 1, 6);

        scrollArea = new QScrollArea(ScenarioEditor);
        scrollArea->setObjectName(QString::fromUtf8("scrollArea"));
        QSizePolicy sizePolicy1(QSizePolicy::Expanding, QSizePolicy::Preferred);
        sizePolicy1.setHorizontalStretch(0);
        sizePolicy1.setVerticalStretch(0);
        sizePolicy1.setHeightForWidth(scrollArea->sizePolicy().hasHeightForWidth());
        scrollArea->setSizePolicy(sizePolicy1);
        scrollArea->setFrameShape(QFrame::NoFrame);
        scrollArea->setWidgetResizable(true);
        scrollArea->setAlignment(Qt::AlignLeading|Qt::AlignLeft|Qt::AlignTop);
        reward = new QWidget();
        reward->setObjectName(QString::fromUtf8("reward"));
        reward->setGeometry(QRect(0, 0, 961, 24));
        QSizePolicy sizePolicy2(QSizePolicy::Preferred, QSizePolicy::Maximum);
        sizePolicy2.setHorizontalStretch(0);
        sizePolicy2.setVerticalStretch(0);
        sizePolicy2.setHeightForWidth(reward->sizePolicy().hasHeightForWidth());
        reward->setSizePolicy(sizePolicy2);
        verticalLayout = new QVBoxLayout(reward);
        verticalLayout->setSpacing(0);
        verticalLayout->setObjectName(QString::fromUtf8("verticalLayout"));
        rewardList = new QStackedWidget(reward);
        rewardList->setObjectName(QString::fromUtf8("rewardList"));

        verticalLayout->addWidget(rewardList);

        scrollArea->setWidget(reward);

        gridLayout->addWidget(scrollArea, 1, 0, 1, 6);

        scrollArea_2 = new QScrollArea(ScenarioEditor);
        scrollArea_2->setObjectName(QString::fromUtf8("scrollArea_2"));
        sizePolicy1.setHeightForWidth(scrollArea_2->sizePolicy().hasHeightForWidth());
        scrollArea_2->setSizePolicy(sizePolicy1);
        scrollArea_2->setFrameShape(QFrame::NoFrame);
        scrollArea_2->setWidgetResizable(true);
        scrollArea_2->setAlignment(Qt::AlignLeading|Qt::AlignLeft|Qt::AlignTop);
        doneList = new QWidget();
        doneList->setObjectName(QString::fromUtf8("doneList"));
        doneList->setGeometry(QRect(0, 0, 961, 24));
        sizePolicy2.setHeightForWidth(doneList->sizePolicy().hasHeightForWidth());
        doneList->setSizePolicy(sizePolicy2);
        verticalLayout_2 = new QVBoxLayout(doneList);
        verticalLayout_2->setSpacing(0);
        verticalLayout_2->setObjectName(QString::fromUtf8("verticalLayout_2"));
        scrollArea_2->setWidget(doneList);

        gridLayout->addWidget(scrollArea_2, 4, 0, 1, 6);

        gridLayout->setRowStretch(1, 1);
        gridLayout->setRowStretch(4, 1);

        retranslateUi(ScenarioEditor);
        QObject::connect(buttonBox, SIGNAL(accepted()), ScenarioEditor, SLOT(accept()));
        QObject::connect(buttonBox, SIGNAL(rejected()), ScenarioEditor, SLOT(reject()));
        QObject::connect(doneFuncUse, SIGNAL(toggled(bool)), doneFunc, SLOT(setEnabled(bool)));
        QObject::connect(rewardFuncUse, SIGNAL(clicked(bool)), rewardFunc, SLOT(setEnabled(bool)));

        QMetaObject::connectSlotsByName(ScenarioEditor);
    } // setupUi

    void retranslateUi(QDialog *ScenarioEditor)
    {
        ScenarioEditor->setWindowTitle(QCoreApplication::translate("ScenarioEditor", "Edit Scenario", nullptr));
        rewardFuncUse->setText(QCoreApplication::translate("ScenarioEditor", "Use script", nullptr));
        label->setText(QCoreApplication::translate("ScenarioEditor", "Player", nullptr));
        doneNodeName->setText(QCoreApplication::translate("ScenarioEditor", "subnodeName", nullptr));
        addDone->setText(QCoreApplication::translate("ScenarioEditor", "Add End Condition", nullptr));
        reloadScripts->setText(QCoreApplication::translate("ScenarioEditor", "Reload Scripts", nullptr));
        addReward->setText(QCoreApplication::translate("ScenarioEditor", "Add Reward", nullptr));
        addDoneNode->setText(QCoreApplication::translate("ScenarioEditor", "Add Sub-Condition", nullptr));
        guess->setText(QCoreApplication::translate("ScenarioEditor", "Guess", nullptr));
        loadScript->setText(QCoreApplication::translate("ScenarioEditor", "Load Script", nullptr));
        doneFuncUse->setText(QCoreApplication::translate("ScenarioEditor", "Use script", nullptr));
    } // retranslateUi

};

namespace Ui {
    class ScenarioEditor: public Ui_ScenarioEditor {};
} // namespace Ui

QT_END_NAMESPACE

#endif // UI_SCENARIOEDITOR_H
