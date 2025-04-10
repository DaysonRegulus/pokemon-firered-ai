/********************************************************************************
** Form generated from reading UI file 'DoneNodeWidget.ui'
**
** Created by: Qt User Interface Compiler version 5.15.3
**
** WARNING! All changes made in this file will be lost when recompiling UI file!
********************************************************************************/

#ifndef UI_DONENODEWIDGET_H
#define UI_DONENODEWIDGET_H

#include <QtCore/QVariant>
#include <QtWidgets/QApplication>
#include <QtWidgets/QFrame>
#include <QtWidgets/QHBoxLayout>
#include <QtWidgets/QRadioButton>
#include <QtWidgets/QToolButton>
#include <QtWidgets/QVBoxLayout>
#include <QtWidgets/QWidget>

QT_BEGIN_NAMESPACE

class Ui_DoneNodeWidget
{
public:
    QHBoxLayout *horizontalLayout_2;
    QFrame *rootLine;
    QVBoxLayout *nodeList;
    QHBoxLayout *horizontalLayout;
    QRadioButton *active;
    QToolButton *remove;
    QFrame *line;
    QRadioButton *conditionAny;
    QRadioButton *conditionAll;

    void setupUi(QWidget *DoneNodeWidget)
    {
        if (DoneNodeWidget->objectName().isEmpty())
            DoneNodeWidget->setObjectName(QString::fromUtf8("DoneNodeWidget"));
        DoneNodeWidget->resize(315, 30);
        horizontalLayout_2 = new QHBoxLayout(DoneNodeWidget);
        horizontalLayout_2->setObjectName(QString::fromUtf8("horizontalLayout_2"));
        horizontalLayout_2->setContentsMargins(-1, 0, 0, 0);
        rootLine = new QFrame(DoneNodeWidget);
        rootLine->setObjectName(QString::fromUtf8("rootLine"));
        rootLine->setFrameShape(QFrame::VLine);
        rootLine->setFrameShadow(QFrame::Sunken);

        horizontalLayout_2->addWidget(rootLine);

        nodeList = new QVBoxLayout();
        nodeList->setSpacing(0);
        nodeList->setObjectName(QString::fromUtf8("nodeList"));
        horizontalLayout = new QHBoxLayout();
        horizontalLayout->setSpacing(12);
        horizontalLayout->setObjectName(QString::fromUtf8("horizontalLayout"));
        active = new QRadioButton(DoneNodeWidget);
        active->setObjectName(QString::fromUtf8("active"));
        QSizePolicy sizePolicy(QSizePolicy::Fixed, QSizePolicy::Fixed);
        sizePolicy.setHorizontalStretch(0);
        sizePolicy.setVerticalStretch(0);
        sizePolicy.setHeightForWidth(active->sizePolicy().hasHeightForWidth());
        active->setSizePolicy(sizePolicy);

        horizontalLayout->addWidget(active);

        remove = new QToolButton(DoneNodeWidget);
        remove->setObjectName(QString::fromUtf8("remove"));

        horizontalLayout->addWidget(remove);

        line = new QFrame(DoneNodeWidget);
        line->setObjectName(QString::fromUtf8("line"));
        QSizePolicy sizePolicy1(QSizePolicy::Fixed, QSizePolicy::Ignored);
        sizePolicy1.setHorizontalStretch(0);
        sizePolicy1.setVerticalStretch(0);
        sizePolicy1.setHeightForWidth(line->sizePolicy().hasHeightForWidth());
        line->setSizePolicy(sizePolicy1);
        line->setFrameShape(QFrame::VLine);
        line->setFrameShadow(QFrame::Sunken);

        horizontalLayout->addWidget(line);

        conditionAny = new QRadioButton(DoneNodeWidget);
        conditionAny->setObjectName(QString::fromUtf8("conditionAny"));
        conditionAny->setChecked(false);

        horizontalLayout->addWidget(conditionAny, 0, Qt::AlignHCenter);

        conditionAll = new QRadioButton(DoneNodeWidget);
        conditionAll->setObjectName(QString::fromUtf8("conditionAll"));

        horizontalLayout->addWidget(conditionAll, 0, Qt::AlignHCenter);


        nodeList->addLayout(horizontalLayout);


        horizontalLayout_2->addLayout(nodeList);


        retranslateUi(DoneNodeWidget);

        QMetaObject::connectSlotsByName(DoneNodeWidget);
    } // setupUi

    void retranslateUi(QWidget *DoneNodeWidget)
    {
        remove->setText(QCoreApplication::translate("DoneNodeWidget", "-", nullptr));
        conditionAny->setText(QCoreApplication::translate("DoneNodeWidget", "Any", nullptr));
        conditionAll->setText(QCoreApplication::translate("DoneNodeWidget", "All", nullptr));
        (void)DoneNodeWidget;
    } // retranslateUi

};

namespace Ui {
    class DoneNodeWidget: public Ui_DoneNodeWidget {};
} // namespace Ui

QT_END_NAMESPACE

#endif // UI_DONENODEWIDGET_H
