/********************************************************************************
** Form generated from reading UI file 'RewardSpecWidget.ui'
**
** Created by: Qt User Interface Compiler version 5.15.3
**
** WARNING! All changes made in this file will be lost when recompiling UI file!
********************************************************************************/

#ifndef UI_REWARDSPECWIDGET_H
#define UI_REWARDSPECWIDGET_H

#include <QtCore/QVariant>
#include <QtWidgets/QApplication>
#include <QtWidgets/QCheckBox>
#include <QtWidgets/QComboBox>
#include <QtWidgets/QDoubleSpinBox>
#include <QtWidgets/QFrame>
#include <QtWidgets/QHBoxLayout>
#include <QtWidgets/QLabel>
#include <QtWidgets/QSpinBox>
#include <QtWidgets/QToolButton>
#include <QtWidgets/QWidget>

QT_BEGIN_NAMESPACE

class Ui_RewardSpecWidget
{
public:
    QHBoxLayout *horizontalLayout;
    QToolButton *remove;
    QFrame *line;
    QLabel *varName;
    QCheckBox *delta;
    QLabel *label;
    QDoubleSpinBox *reward;
    QLabel *label_2;
    QDoubleSpinBox *penalty;
    QLabel *label_3;
    QComboBox *operation;
    QSpinBox *reference;

    void setupUi(QWidget *RewardSpecWidget)
    {
        if (RewardSpecWidget->objectName().isEmpty())
            RewardSpecWidget->setObjectName(QString::fromUtf8("RewardSpecWidget"));
        RewardSpecWidget->resize(911, 31);
        horizontalLayout = new QHBoxLayout(RewardSpecWidget);
        horizontalLayout->setObjectName(QString::fromUtf8("horizontalLayout"));
        horizontalLayout->setContentsMargins(0, 0, 0, 0);
        remove = new QToolButton(RewardSpecWidget);
        remove->setObjectName(QString::fromUtf8("remove"));

        horizontalLayout->addWidget(remove);

        line = new QFrame(RewardSpecWidget);
        line->setObjectName(QString::fromUtf8("line"));
        line->setFrameShape(QFrame::VLine);
        line->setFrameShadow(QFrame::Sunken);

        horizontalLayout->addWidget(line);

        varName = new QLabel(RewardSpecWidget);
        varName->setObjectName(QString::fromUtf8("varName"));
        QFont font;
        font.setItalic(true);
        varName->setFont(font);

        horizontalLayout->addWidget(varName);

        delta = new QCheckBox(RewardSpecWidget);
        delta->setObjectName(QString::fromUtf8("delta"));
        delta->setChecked(true);

        horizontalLayout->addWidget(delta);

        label = new QLabel(RewardSpecWidget);
        label->setObjectName(QString::fromUtf8("label"));

        horizontalLayout->addWidget(label);

        reward = new QDoubleSpinBox(RewardSpecWidget);
        reward->setObjectName(QString::fromUtf8("reward"));
        reward->setAccelerated(true);
        reward->setDecimals(5);
        reward->setMinimum(-1000000000.000000000000000);
        reward->setMaximum(1000000000.000000000000000);

        horizontalLayout->addWidget(reward);

        label_2 = new QLabel(RewardSpecWidget);
        label_2->setObjectName(QString::fromUtf8("label_2"));

        horizontalLayout->addWidget(label_2);

        penalty = new QDoubleSpinBox(RewardSpecWidget);
        penalty->setObjectName(QString::fromUtf8("penalty"));
        penalty->setAccelerated(true);
        penalty->setDecimals(5);
        penalty->setMinimum(-1000000000.000000000000000);
        penalty->setMaximum(1000000000.000000000000000);

        horizontalLayout->addWidget(penalty);

        label_3 = new QLabel(RewardSpecWidget);
        label_3->setObjectName(QString::fromUtf8("label_3"));

        horizontalLayout->addWidget(label_3);

        operation = new QComboBox(RewardSpecWidget);
        operation->setObjectName(QString::fromUtf8("operation"));

        horizontalLayout->addWidget(operation);

        reference = new QSpinBox(RewardSpecWidget);
        reference->setObjectName(QString::fromUtf8("reference"));
        reference->setMinimum(-2147483647);
        reference->setMaximum(2147483647);

        horizontalLayout->addWidget(reference);


        retranslateUi(RewardSpecWidget);

        QMetaObject::connectSlotsByName(RewardSpecWidget);
    } // setupUi

    void retranslateUi(QWidget *RewardSpecWidget)
    {
        RewardSpecWidget->setWindowTitle(QCoreApplication::translate("RewardSpecWidget", "Form", nullptr));
        remove->setText(QCoreApplication::translate("RewardSpecWidget", "-", nullptr));
        varName->setText(QCoreApplication::translate("RewardSpecWidget", "{varName}", nullptr));
        delta->setText(QCoreApplication::translate("RewardSpecWidget", "delta", nullptr));
        label->setText(QCoreApplication::translate("RewardSpecWidget", "gives", nullptr));
        label_2->setText(QCoreApplication::translate("RewardSpecWidget", "reward and", nullptr));
        label_3->setText(QCoreApplication::translate("RewardSpecWidget", "penalty", nullptr));
    } // retranslateUi

};

namespace Ui {
    class RewardSpecWidget: public Ui_RewardSpecWidget {};
} // namespace Ui

QT_END_NAMESPACE

#endif // UI_REWARDSPECWIDGET_H
